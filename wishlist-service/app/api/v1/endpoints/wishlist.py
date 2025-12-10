from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated
from sqlmodel import Session, select
from app.database import get_session
from app.models import Wishlist, WishlistItem, WishlistRead, WishlistItemCreate, WishlistItemRead
from app.product_client import product_client
from app.shop_client import shop_client
import httpx
from app.rabbitmq.publisher import event_publisher
from dotenv import load_dotenv
import os

load_dotenv()


SHOPCART_SERVICE_URL = os.getenv('SHOPCART_SERVICE_URL')

router = APIRouter()

def get_user_id(user_id: str = Header(None, alias="X-User-Id", include_in_schema=False)):
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in request headers"
        )
    return user_id


@router.post("/wishlist", response_model=WishlistItemRead, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    item_data: WishlistItemCreate, 
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    # Get or create the user's wishlist container
    wishlist = session.exec(
        select(Wishlist).where(Wishlist.user_id == user_id)
    ).first()
    
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        session.add(wishlist)
        session.commit()
        session.refresh(wishlist)

    # Validate and create the wishlist item
    if item_data.product_variation_id:
        product_data = await product_client.get_product_data_by_variation_id(item_data.product_variation_id)
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product variation not found in Product Service"
            )
        
        # Check if product already in wishlist
        existing = session.exec(
            select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_variation_id == item_data.product_variation_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product already in wishlist"
            )
        
        db_item = WishlistItem(
            wishlist_id=wishlist.id,
            product_variation_id=item_data.product_variation_id
        )
    
    elif item_data.shop_id:
        shop_data = await shop_client.get_shop_data(item_data.shop_id)
        if not shop_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found in Shop Service"
            )
        
        # Check if shop already in wishlist
        existing = session.exec(
            select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.shop_id == item_data.shop_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop already in wishlist"
            )
        
        db_item = WishlistItem(
            wishlist_id=wishlist.id,
            shop_id=item_data.shop_id
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either product_variation_id or shop_id must be provided"
        )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    await event_publisher.publish_wishlist_created(
        wishlist_id=db_item.id,
        user_id=user_id,
        product_variation_id=item_data.product_variation_id,
        shop_id=item_data.shop_id
    )
    
    return db_item

@router.post("/wishlist/{item_id}/move-to-cart")
async def move_to_cart(
    item_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """Move a product from wishlist to shopping cart"""
    
    # Get the wishlist item
    wishlist_item = session.get(WishlistItem, item_id)
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    # Verify ownership
    wishlist = session.get(Wishlist, wishlist_item.wishlist_id)
    if not wishlist or wishlist.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only move your own wishlist items"
        )
    
    # Only products can be moved to cart (not shops)
    if not wishlist_item.product_variation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only products can be moved to cart. Shops cannot be added to cart."
        )
    
    # Verify product is still active and available
    product_data = await product_client.get_product_data_by_variation_id(
        wishlist_item.product_variation_id
    )
    if not product_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product no longer available"
        )
    
    # Call ShopCart service to add item
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SHOPCART_SERVICE_URL}/api/items/{wishlist_item.product_variation_id}",
                json={},
                headers={"X-User-Id": user_id}
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shopping cart not found. Please create a cart first."
                )
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Bad request')
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to add to cart: {error_detail}"
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ShopCart service unavailable"
                )
            
            cart_item_data = response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to ShopCart service: {str(e)}"
        )
    
    # Remove from wishlist after successfully adding to cart
    session.delete(wishlist_item)
    session.commit()
    
    # Publish event
    await event_publisher.publish_wishlist_deleted(
        wishlist_id=item_id,
        user_id=user_id
    )
    
    return {
        "message": "Item successfully moved to cart",
        "cart_item": cart_item_data,
        "removed_from_wishlist": item_id
    }


@router.delete("/wishlist/{item_id}")
async def remove_from_wishlist(
    item_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    # Get the wishlist item
    wishlist_item = session.get(WishlistItem, item_id)
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    # Get the wishlist to verify ownership
    wishlist = session.get(Wishlist, wishlist_item.wishlist_id)
    
    if not wishlist or wishlist.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own wishlist items"
        )
    
    session.delete(wishlist_item)
    session.commit()
    
    await event_publisher.publish_wishlist_deleted(
        wishlist_id=item_id,
        user_id=user_id
    )
    
    return {"message": "Item removed from wishlist successfully"}


@router.get("/wishlist", response_model=WishlistRead)
async def get_wishlist(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """Get user's complete wishlist with all items"""
    wishlist = session.exec(
        select(Wishlist).where(Wishlist.user_id == user_id)
    ).first()
    
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found. Please contact support."
        )
    
    return wishlist


@router.get("/wishlist/count")
async def get_wishlist_count(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """Get count of items in user's wishlist"""
    wishlist = session.exec(
        select(Wishlist).where(Wishlist.user_id == user_id)
    ).first()
    
    if not wishlist:
        return {"user_id": user_id, "wishlist_count": 0}
    
    items = session.exec(
        select(WishlistItem).where(WishlistItem.wishlist_id == wishlist.id)
    ).all()
    
    return {"user_id": user_id, "wishlist_count": len(items)}
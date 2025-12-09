from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated
from sqlmodel import Session, select
from app.database import get_session
from app.models import Wishlist, WishlistItem, WishlistRead, WishlistItemCreate, WishlistItemRead
from app.product_client import product_client
from app.shop_client import shop_client

from app.rabbitmq.publisher import event_publisher

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
        # Create empty wishlist if doesn't exist
        wishlist = Wishlist(user_id=user_id)
        session.add(wishlist)
        session.commit()
        session.refresh(wishlist)
    
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
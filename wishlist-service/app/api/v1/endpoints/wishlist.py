from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated
from sqlmodel import Session, select
from app.database import get_session
from app.models import Wishlist, WishlistCreate, WishlistResponse, WishlistListResponse
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


@router.post("/wishlist", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    wishlist: WishlistCreate, 
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):

    if wishlist.product_variation_id:
        product_data = await product_client.get_product_data_by_variation_id(wishlist.product_variation_id)
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product variation not found in Product Service"
            )
        existing = session.exec(
            select(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.product_variation_id == wishlist.product_variation_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product already in wishlist"
            )
        db_wishlist = Wishlist(
            user_id=user_id,
            product_variation_id=wishlist.product_variation_id
        )
    
    elif wishlist.shop_id:
        shop_data = await shop_client.get_shop_data(wishlist.shop_id)
        if not shop_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found in Shop Service"
            )
        existing = session.exec(
            select(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.shop_id == wishlist.shop_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop already in wishlist"
            )
        db_wishlist = Wishlist(
            user_id=user_id,
            shop_id=wishlist.shop_id
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either product_variation_id or shop_id must be provided"
        )

    session.add(db_wishlist)
    session.commit()
    session.refresh(db_wishlist)

    await event_publisher.publish_wishlist_created(
        wishlist_id=db_wishlist.id, # type: ignore
        user_id=user_id,
        product_variation_id=wishlist.product_variation_id,
        shop_id=wishlist.shop_id
    )
    
    return db_wishlist


@router.delete("/wishlist/{item_id}")
async def remove_from_wishlist(
    item_id: int,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):

    wishlist_item = session.get(Wishlist, item_id)
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    if wishlist_item.user_id != user_id:
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


@router.get("/wishlist", response_model=list[WishlistResponse])
async def get_wishlist_items(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    
    wishlist_items = session.exec(
        select(Wishlist).where(Wishlist.user_id == user_id)
    ).all()
    
    return wishlist_items


@router.get("/wishlist/count")
async def get_wishlist_count(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    
    count = session.exec(
        select(Wishlist).where(Wishlist.user_id == user_id)
    ).all()
    
    return {"user_id": user_id, "wishlist_count": len(count)}
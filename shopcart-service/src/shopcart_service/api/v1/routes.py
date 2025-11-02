from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Header
from sqlalchemy.orm import Session
import logging
from src.shopcart_service import crud, schemas
from src.shopcart_service.core import db
from src.shopcart_service import models
from pydantic import UUID4
from src.shopcart_service.core.product_client import product_client
from uuid import UUID
from ...core.product_client import ProductServiceDataCheck
product_client = ProductServiceDataCheck()


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shopcart/api", tags=["Cart"])

def get_user_id(user_id: str = Header(None, alias="X-User-Id", include_in_schema=False)):
    """Extract user ID from X-User-Id header"""
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="User ID not found in request headers"
        )
    return user_id


# def verify_cart_ownership(db: Session, cart_id: int, user_uuid: str):
#     """Verify that the cart belongs to the user"""
#     cart = db.query(models.ShopCart).filter(
#         models.ShopCart.id == cart_id,
#         models.ShopCart.user_uuid == user_uuid
#     ).first()
    
#     if not cart:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have access to this cart"
#         )
#     return cart


@router.post("/", response_model=schemas.ShopCartRead)
def create_cart(user_uuid: str = Depends(get_user_id), db: Session = Depends(db.get_db)):
    existing_cart = crud.get_user_by_uuid(db,user_uuid)
    if existing_cart:   
        raise HTTPException(status_code = 401 , detail = "You have already got a shop cart")
    
    new_cart = crud.create_cart(db, user_uuid)
    if not new_cart:
        raise HTTPException(
            status_code=400,
            detail="Could not create cart. You might be a shop owner."
        )
    return new_cart



@router.get("/mycart", response_model=schemas.ShopCartRead)
def get_cart(user_uuid: str = Depends(get_user_id), db: Session = Depends(db.get_db)):
    cart = crud.get_cart(db, user_uuid)
    if not cart:
        raise HTTPException(
            status_code=404,
            detail="No cart found. Shop owners cannot have shopping carts."
        )
    return cart


@router.post("/items/{product_var_id}", response_model=schemas.CartItemRead)
async def add_item(
    product_var_id: UUID, 
    item: schemas.CartItemCreate, 
    user_uuid: str = Depends(get_user_id),
    db: Session = Depends(db.get_db)
):
    
    cart = crud.get_cart(db, user_uuid)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    logger.info(f'Add item request - Cart ID: {cart.id}, Product variation ID: {product_var_id}, User: {user_uuid}')
    
    logger.info(f'Calling product_client.get_product_data_by_variation_id({product_var_id})')
    product_data = await product_client.verify_product_exists(product_var_id)
    logger.info(f'Product client returned data: {product_data}')
    
    if not product_data:
        logger.warning(f'Product not found for variation ID: {product_var_id}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_var_id} not found in Product Service."
        )
    
    await product_client.verify_stock(product_var_id, 1)

    
    logger.info(f'Adding item to cart - Cart ID: {cart.id}')
    return crud.add_item_to_cart(db, product_var_id, cart.id, item)



@router.put("/items/{item_id}", response_model=schemas.CartItemRead)
async def update_cart_item(
    item_id: int, 
    item: schemas.CartItemUpdate, 
    user_uuid: str = Depends(get_user_id),
    db: Session = Depends(db.get_db)
):
    # Get user's cart
    cart = crud.get_cart(db, user_uuid)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Verify stock for new quantity
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.shop_cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    await product_client.verify_stock(cart_item.product_variation_id, item.quantity)
    
    # Update
    return crud.update_cart(db, item_id, cart.id, item)



@router.delete("/items/{item_id}",response_model = schemas.CartItemRead)
def delete_cart_item(
    item_id: int, 
    user_uuid: str = Depends(get_user_id),
    db: Session = Depends(db.get_db)
):
    cart = crud.get_cart(db, user_uuid)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    deleted_item = crud.delete_cart_item(db, item_id, cart.id)
    if not deleted_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return deleted_item



from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.params import Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import httpx
import os
from src.app.core.db import get_db
from src.app.core.db import SessionLocal
from src.app.core.config import SHOP_SERVICE_URL
from src.app.core.shop_client import shop_client
# Repositories
from src.app.repositories.v1.category import CategoryRepository
from src.app.repositories.v1.product import ProductRepository
from src.app.repositories.v1.product_variation import ProductVariationRepository
from src.app.repositories.v1.product_image import ProductImageRepository
from src.app.repositories.v1.comment import CommentRepository
# Schemas
from src.app.schemas.v1.category import CategoryCreate, Category
from src.app.schemas.v1.product import ProductCreate, Product
from src.app.schemas.v1.product_variation import ProductVariationCreate, ProductVariation
from src.app.schemas.v1.product_image import ProductImageCreate, ProductImage
from src.app.schemas.v1.comment import CommentCreate, Comment
from src.app.publisher import rabbitmq_publisher

# Cache
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from src.app.cache.key_builders import (
    product_list_key_builder,
    product_detail_key_builder,
    variation_list_key_builder,
    variation_detail_key_builder,
)

from src.app.cache.invalidation import (
    invalidate_product,
    invalidate_variation,
)

from src.app.authorization.shop_permission import ShopPermission
from src.app.authorization.comment_permission import CommentPermission

router = APIRouter()
# Endpoints for Category
@router.post("/categories/", response_model=Category)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    return repo.create(category)


@router.get("/categories/", response_model=List[Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    return repo.get_all(skip, limit)


@router.get("/categories/{category_id}", response_model=Category)
def read_category(category_id: UUID, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    category = repo.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: UUID, category: CategoryCreate, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    updated_category = repo.update(category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@router.delete("/categories/{category_id}")
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    if not repo.delete(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

# Endpoints for Product
@router.post("/products/", response_model=Product)
async def create_product(
    product: ProductCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    ):
    user_id = request.headers.get('x-user-id')
    if not user_id:
        raise HTTPException(
            status_code=400, 
            detail="User ID not provided in headers"
        )
    # shop_id = await shop_client.get_shop_by_user_id(user_id)
    shop_id = request.headers.get('x-shop-id')

    if not shop_id:
        raise HTTPException(
            status_code=400, 
            detail="User does not have a shop"
        )
    repo = ProductRepository(db)
    try:
        result = repo.create_with_categories(product, shop_id)
        # invalidate all product list caches
        background_tasks.add_task(invalidate_product, str(result.id))
        # Publish product created event to RabbitMQ
        product_dict = {
            'id': result.id,
            'shop_id': result.shop_id,
            'title': result.title,
            'about': result.about,
            'on_sale': result.on_sale,
            'is_active': result.is_active,
            'top_sale': result.top_sale,
            'top_popular': result.top_popular,
            'sku': result.sku,
            'created_at': result.created_at,
        }
        rabbitmq_publisher.publish_product_created(product_dict)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

from datetime import datetime

@router.get("/products/")
@cache(expire=60, key_builder=product_list_key_builder)
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return {
        "timestamp": datetime.now().isoformat(),
        "data": ProductRepository(db).get_all(skip, limit)
    }


@router.get("/products/{product_id}", response_model=Product)
@cache(expire=120, key_builder=product_detail_key_builder)
def read_product(product_id: UUID, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    product = repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: UUID,
    product: ProductCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        # raise HTTPException(
        #     status_code=400,
        #     detail="User ID not provided in headers"
        # )
        raise HTTPException(400, "User ID not provided in headers")


    # repo = ProductRepository(db)
    
    # Get existing product to verify ownership
    # existing_product = repo.get(product_id)
    # if not existing_product:
    #     raise HTTPException(status_code=404, detail="Product not found")
        
    # # Verify product belongs to user's shop
    # shop_id = await shop_client.get_shop_by_user_id(user_id)
    # if not shop_id or str(existing_product.shop_id) != str(shop_id):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Not authorized to update this product"
    #     )
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID not provided in token/header")
    
    # Initialize authorization helper
    perm = ShopPermission(db, shop_id)

    # Check ownership
    perm.check_product_owner(product_id)

    repo = ProductRepository(db)

    try:
        updated = repo.update_with_categories(product_id, product)
        if not updated:
            raise HTTPException(404, "Product not found")
        
        product_dict = {
        'id': updated.id,
        'shop_id': updated.shop_id,
        'title': updated.title,
        'about': updated.about,
        'on_sale': updated.on_sale,
        'is_active': updated.is_active,
        'top_sale': updated.top_sale,
        'top_popular': updated.top_popular,
        'sku': updated.sku,
        'created_at': updated.created_at,
        }
        rabbitmq_publisher.publish_product_updated(product_dict)
        
        background_tasks.add_task(invalidate_product, str(product_id))

        return updated
    except ValueError as e:
        # raise HTTPException(
        #     status_code=400,
        #     detail=str(e)
        # )
        raise HTTPException(400, str(e))



@router.patch("/products/{product_id}", response_model=Product)
async def partial_update_product(
    product_id: UUID,
    product_data: dict,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # user_id = request.headers.get('x-user-id')
    # if not user_id:
    #     raise HTTPException(status_code=401, detail="User ID required")

    # repo = ProductRepository(db)

    # existing_product = repo.get(product_id)
    # if not existing_product:
    #     raise HTTPException(status_code=404, detail="Product not found")

    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing")

    # shop_id = await shop_client.get_shop_by_user_id(user_id)
    # if not shop_id or str(existing_product.shop_id) != str(shop_id):
    #     raise HTTPException(status_code=403, detail="You can only update your own products")

    permission = ShopPermission(db, shop_id)
    permission.check_product_owner(product_id)

    repo = ProductRepository(db)

    updated = repo.update(product_id, product_data)
    if updated:
        product_dict = {
            'id': updated.id,
            'shop_id': updated.shop_id,
            'title': updated.title,
            'about': updated.about,
            'on_sale': updated.on_sale,
            'is_active': updated.is_active,
            'top_sale': updated.top_sale,
            'top_popular': updated.top_popular,
            'sku': updated.sku,
            'created_at': updated.created_at,
        }
        rabbitmq_publisher.publish_product_updated(product_dict)

    background_tasks.add_task(invalidate_product, str(product_id))

    return updated


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # repo = ProductRepository(db)
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing")

    # existing = repo.get(product_id)
    # if not existing:
    #     raise HTTPException(status_code=404, detail="Product not found")

    permission = ShopPermission(db, shop_id)
    permission.check_product_owner(product_id)

    repo = ProductRepository(db)
    repo.delete(product_id)
    rabbitmq_publisher.publish_product_deleted(product_id)

    background_tasks.add_task(invalidate_product, str(product_id))

    return {"message": "Product deleted"}


# Endpoints for ProductVariation
@router.post("/products/{product_id}/variations/", response_model=ProductVariation)
def create_product_variation(
    product_id: UUID,
    variation: ProductVariationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Get shop_id from token header
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    # Authorization layer
    permission = ShopPermission(db, shop_id)
    permission.check_product_owner(product_id)
    repo = ProductVariationRepository(db)
    variation_data = variation.dict()
    variation_data["product_id"] = product_id

    new_variation = repo.create(variation_data)

    background_tasks.add_task(invalidate_variation, str(new_variation.id), db)

    return new_variation



@router.get("/products/{product_id}/variations/", response_model=List[ProductVariation])
@cache(expire=60, key_builder=variation_list_key_builder)
def read_product_variations(product_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    variations = repo.get_variations_by_product(product_id, skip, limit)
    return variations


@router.get("/products/variations/{variation_id}", response_model=ProductVariation)
@cache(expire=120, key_builder=variation_detail_key_builder)
def read_product_variation(variation_id: UUID, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    variation = repo.get(variation_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return variation


@router.put("/products/variations/{variation_id}", response_model=ProductVariation)
def update_product_variation(
    variation_id: UUID,
    variation: ProductVariationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    # Permission check (variation → product owner)
    permission = ShopPermission(db, shop_id)
    permission.check_variation_owner(variation_id)
    repo = ProductVariationRepository(db)
    updated_variation = repo.update(variation_id, variation)

    if not updated_variation:
        raise HTTPException(404, "Variation not found")

    background_tasks.add_task(invalidate_variation, str(variation_id), db)

    return updated_variation



# #Useless endpoints for now so, don't implement invalidation
# @router.put("/products/variations/{variation_id}/decrease-amount", response_model=ProductVariation)
# async def decrease_variation_amount(
#     variation_id: UUID,
#     request: Request,
#     quantity: int = Query(..., gt=0, description="Amount to decrease"),  # required query param
#     db: Session = Depends(get_db)
# ):
#     """
#     Decrease the available amount of a product variation.
#     """
#     user_id = request.headers.get("x-user-id")
#     if not user_id:
#         raise HTTPException(status_code=400, detail="User ID not provided")

#     repo = ProductVariationRepository(db)
#     updated_variation = repo.decrease_amount(variation_id, quantity)
#     return updated_variation


# @router.put("/products/variations/{variation_id}/increase-amount", response_model=ProductVariation)
# async def increase_variation_amount(
#     variation_id: UUID,
#     request: Request,
#     quantity: int = Query(..., gt=0, description="Amount to increase"),  # required query param
#     db: Session = Depends(get_db)
# ):
#     """
#     Increase the available amount of a product variation.
#     """
#     user_id = request.headers.get("x-user-id")
#     if not user_id:
#         raise HTTPException(status_code=400, detail="User ID not provided")

#     repo = ProductVariationRepository(db)
#     updated_variation = repo.increase_amount(variation_id, quantity)
#     return updated_variation


@router.delete("/products/variations/{variation_id}")
def delete_product_variation(
    variation_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    # Permission check
    permission = ShopPermission(db, shop_id)
    permission.check_variation_owner(variation_id)
    repo = ProductVariationRepository(db)

    # check first
    existing = repo.get(variation_id)
    if not existing:
        raise HTTPException(404, "Variation not found")

    repo.delete(variation_id)

    background_tasks.add_task(invalidate_variation, str(variation_id), db)

    return {"message": "Variation deleted"}


# Endpoints for ProductImage
@router.post("/products/variations/{variation_id}/images/")
async def create_product_image(
    variation_id: UUID,
    image: ProductImageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    permission = ShopPermission(db, shop_id)

    await permission.check_variation_owner(variation_id)

    repo = ProductImageRepository(db)
    image_data = image.dict()
    image_data["product_variation_id"] = variation_id
    new_image = repo.create(image_data)

    background_tasks.add_task(invalidate_variation, str(variation_id), db)

    return new_image



@router.get("/products/variations/{variation_id}/images/", response_model=List[ProductImage])
def read_product_images(variation_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProductImageRepository(db)
    return repo.get_by_variation(variation_id, skip, limit)




@router.get("/products/images/{image_id}", response_model=ProductImage)
def get_product_image(image_id: UUID, db: Session = Depends(get_db)):
    repo = ProductImageRepository(db)

    image = repo.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return image



@router.put("/products/images/{image_id}", response_model=ProductImage)
async def update_product_image(
    image_id: UUID,
    update_data: ProductImageCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    permission = ShopPermission(db, shop_id)
    await permission.check_image_owner(image_id)

    repo = ProductImageRepository(db)
    updated = repo.update(image_id, update_data)

    if not updated:
        raise HTTPException(404, "Image not found")

    return updated


@router.delete("/products/variations/images/{image_id}")
async def delete_product_image(
    image_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    shop_id = request.headers.get("x-shop-id")
    if not shop_id:
        raise HTTPException(401, "Shop ID missing in token/header")

    # Authorization
    permission = ShopPermission(db, shop_id)
    await permission.check_image_owner(image_id)

    repo = ProductImageRepository(db)

    deleted = repo.delete(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"message": "Image deleted"}


# Endpoints for Comment
@router.post("/products/variations/{variation_id}/comments/", response_model=Comment)
async def create_comment(
    variation_id: UUID,
    comment: CommentCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not provided in headers")
    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    comment_data = comment.dict()
    comment_data["product_variation_id"] = variation_id
    comment_data["user_id"] = user_id

    repo = CommentRepository(db)
    new_comment = repo.create(comment_data)

    background_tasks.add_task(
        invalidate_variation,
        str(variation_id),
        db
    )

    # 6. Return created comment immediately
    return new_comment



@router.get("/products/variations/{variation_id}/comments/", response_model=List[Comment])
def read_comments(variation_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = CommentRepository(db)
    return repo.get_by_variation(variation_id, skip, limit)


@router.get("/products/comments/{comment_id}", response_model=Comment)
def read_comment(comment_id: UUID, db: Session = Depends(get_db)):
    repo = CommentRepository(db)
    comment = repo.get(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.put("/products/comments/{comment_id}", response_model=Comment)
def update_comment(
    comment_id: UUID,
    update_data: CommentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(401, "User ID required")

    # Authorization
    permission = CommentPermission(db, user_id)
    permission.check_comment_owner(comment_id)

    repo = CommentRepository(db)
    updated = repo.update(comment_id, update_data)

    if not updated:
        raise HTTPException(404, "Comment not found")

    return updated


@router.delete("/products/comments/{comment_id}")
def delete_comment(
    comment_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(401, "User ID required")

    # Authorization
    permission = CommentPermission(db, user_id)
    permission.check_comment_owner(comment_id)

    repo = CommentRepository(db)

    deleted = repo.delete(comment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"message": "Comment deleted"}
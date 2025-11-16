from fastapi import APIRouter, HTTPException, Depends, Request
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
async def create_product(product: ProductCreate, request: Request, db: Session = Depends(get_db)):
    user_id = request.headers.get('x-user-id')
    if not user_id:
        raise HTTPException(
            status_code=400, 
            detail="User ID not provided in headers"
        )
    shop_id = await shop_client.get_shop_by_user_id(user_id)
    if not shop_id:
        raise HTTPException(
            status_code=400, 
            detail="User does not have a shop"
        )
    repo = ProductRepository(db)
    try:
        result = repo.create_with_categories(product, shop_id)
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


@router.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    return repo.get_all(skip, limit)


@router.get("/products/{product_id}", response_model=Product)
def read_product(product_id: UUID, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    product = repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=Product)
def update_product(product_id: UUID, product: ProductCreate, request: Request, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    updated_product = repo.update(product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Publish product updated event to RabbitMQ
    product_dict = {
        'id': updated_product.id,
        'shop_id': updated_product.shop_id,
        'title': updated_product.title,
        'about': updated_product.about,
        'on_sale': updated_product.on_sale,
        'is_active': updated_product.is_active,
        'top_sale': updated_product.top_sale,
        'top_popular': updated_product.top_popular,
        'sku': updated_product.sku,
        'created_at': updated_product.created_at,
    }
    rabbitmq_publisher.publish_product_updated(product_dict)
    return updated_product
        
@router.patch("/products/{product_id}", response_model=Product)
async def partial_update_product(product_id: UUID, product_data: dict, request: Request, db: Session = Depends(get_db)):
    user_id = request.headers.get('x-user-id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    repo = ProductRepository(db)
    existing_product = repo.get(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    shop_id = await shop_client.get_shop_by_user_id(user_id)
    if not shop_id or str(existing_product.shop_id) != str(shop_id):
        raise HTTPException(status_code=403, detail="You can only update your own products")
    
    updated_product = repo.update(product_id, product_data)
    # Publish product updated event to RabbitMQ
    if updated_product:
        product_dict = {
            'id': updated_product.id,
            'shop_id': updated_product.shop_id,
            'title': updated_product.title,
            'about': updated_product.about,
            'on_sale': updated_product.on_sale,
            'is_active': updated_product.is_active,
            'top_sale': updated_product.top_sale,
            'top_popular': updated_product.top_popular,
            'sku': updated_product.sku,
            'created_at': updated_product.created_at,
        }
        rabbitmq_publisher.publish_product_updated(product_dict)
    return updated_product


@router.delete("/products/{product_id}")
def delete_product(product_id: UUID, db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    if not repo.delete(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    # Publish product deleted event to RabbitMQ
    rabbitmq_publisher.publish_product_deleted(product_id)
    return {"message": "Product deleted"}


# Endpoints for ProductVariation
@router.post("/products/{product_id}/variations/", response_model=ProductVariation)
def create_product_variation(product_id: UUID, variation: ProductVariationCreate, db: Session = Depends(get_db)): # Can be eliminated(product_id)
    repo = ProductVariationRepository(db)
    result = repo.create(variation)
    return result


@router.get("/products/{product_id}/variations/", response_model=List[ProductVariation])
def read_product_variations(product_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    variations = repo.get_all(skip, limit)
    return [v for v in variations if v.product_id == product_id]  # Filter by product_id


@router.get("/products/variations/{variation_id}", response_model=ProductVariation)
def read_product_variation(variation_id: UUID, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    variation = repo.get(variation_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return variation

@router.put("/products/variations/{variation_id}", response_model=ProductVariation)
def update_product_variation(variation_id: UUID, variation: ProductVariationCreate, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    updated_variation = repo.update(variation_id, variation)
    if not updated_variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return updated_variation


@router.delete("/products/variations/{variation_id}")
def delete_product_variation(variation_id: UUID, db: Session = Depends(get_db)):
    repo = ProductVariationRepository(db)
    variation = repo.get(variation_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    if not repo.delete(variation_id):
        raise HTTPException(status_code=404, detail="Variation not found")
    return {"message": "Variation deleted"}


# Endpoints for ProductImage
@router.post("/products/variations/{variation_id}/images/")
def create_product_image(variation_id: UUID, image: ProductImageCreate, db: Session = Depends(get_db)):
    repo = ProductImageRepository(db)
    image_data = image.dict()
    image_data["product_variation_id"] = variation_id
    return repo.create(image_data)


@router.get("/products/variations/{variation_id}/images/", response_model=List[ProductImage])
def read_product_images(variation_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProductImageRepository(db)
    return repo.get_by_variation(variation_id, skip, limit)


@router.delete("/products/variations/{variation_id}/images/{image_id}") # Can remove variation_id from the path if not needed
def delete_product_image(variation_id: UUID, image_id: UUID, db: Session = Depends(get_db)):
    repo = ProductImageRepository(db)
    if not repo.delete(image_id):
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted"}


# Endpoints for Comment
@router.post("/products/variations/{variation_id}/comments/", response_model=Comment)
async def create_comment(
    variation_id: UUID,
    comment: CommentCreate,
    request: Request,
    db: Session = Depends(get_db)
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
    return repo.create(comment_data)


@router.get("/products/variations/{variation_id}/comments/", response_model=List[Comment])
def read_comments(variation_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = CommentRepository(db)
    return repo.get_by_variation(variation_id, skip, limit)
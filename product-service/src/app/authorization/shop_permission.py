from fastapi import HTTPException
from src.app.models.v1 import Product, ProductVariation, ProductImage


class ShopPermission:
    def __init__(self, db_session, shop_id):
        self.db = db_session
        self.shop_id = str(shop_id)

    def check_product_owner(self, product_id):
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.shop_id == self.shop_id)
            .first()
        )

        if not product:
            raise HTTPException(403, "Product not found or not owned by your shop")

    def check_variation_owner(self, variation_id):
        variation = (
            self.db.query(ProductVariation)
            .join(Product, Product.id == ProductVariation.product_id)
            .filter(
                ProductVariation.id == variation_id,
                Product.shop_id == self.shop_id
            )
            .first()
        )

        if not variation:
            raise HTTPException(403, "Variation not found or not owned by your shop")

    def check_image_owner(self, image_id):
        image = (
            self.db.query(ProductImage)
            .join(ProductVariation, ProductVariation.id == ProductImage.product_variation_id)
            .join(Product, Product.id == ProductVariation.product_id)
            .filter(
                ProductImage.id == image_id,
                Product.shop_id == self.shop_id
            )
            .first()
        )

        if not image:
            raise HTTPException(403, "Image not found or not owned by your shop")
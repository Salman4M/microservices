from pydantic import BaseModel #model_validator for validation in our schemas
from datetime import datetime
from typing import List, Optional
from pydantic import UUID4


class CartItemBase(BaseModel):
    quantity: int = 1

class CartItemCreate(BaseModel):
    pass

class CartItemRead(CartItemBase):
    id: int
    product_variation_id: UUID4
    quantity: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ShopCartBase(BaseModel):
    user_uuid: UUID4

class ShopCartCreate(ShopCartBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int

class ShopCartRead(ShopCartBase):
    id: int
    items: List[CartItemRead] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

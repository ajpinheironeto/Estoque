from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


class ProductCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    sku: Optional[constr(strip_whitespace=True)] = None
    price: float = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    description: Optional[str] = None
    category: Optional[str] = None


class Product(ProductCreate):
    id: int
    created_at: datetime

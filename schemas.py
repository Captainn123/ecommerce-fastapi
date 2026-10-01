from pydantic import BaseModel
from typing import Optional

# This is the data we expect the user to send when creating a product
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0

# This is the data the API will return back to the user
class ProductResponse(ProductCreate):
    id: int
    is_active: bool

    # This tells Pydantic to read data from our SQLAlchemy database models
    class Config:
        from_attributes = True

# --- USER SCHEMAS ---

# Data we expect from the user when they sign up
class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "customer"

# Data we send back (Notice we DO NOT send the password back!)
class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    role: str


    class Config:
        from_attributes = True

from typing import List

# --- ORDER SCHEMAS ---

# A single item in the shopping cart
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

# The full order requested by the user
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

# What the API returns after a successful order
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str

    class Config:
        from_attributes = True
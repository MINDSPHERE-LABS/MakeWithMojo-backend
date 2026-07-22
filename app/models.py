from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    title: str
    slug: str
    short_description: str
    description: str
    price: float
    discount_price: Optional[float] = None
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    thumbnail: str
    gallery: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    available_colors: List[str] = Field(default_factory=list)
    available_sizes: List[str] = Field(default_factory=list)
    material: str
    print_quality: str
    production_time: str
    stock: int
    SKU: str
    weight: float
    dimensions: str  # Format: "LxWxH cm" or similar
    shipping_weight: float
    rating: float = 0.0
    review_count: int = 0
    sales: int = 0
    views: int = 0
    featured: bool = False
    new_arrival: bool = False
    best_seller: bool = False
    published: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail: Optional[str] = None
    gallery: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    available_colors: Optional[List[str]] = None
    available_sizes: Optional[List[str]] = None
    material: Optional[str] = None
    print_quality: Optional[str] = None
    production_time: Optional[str] = None
    stock: Optional[int] = None
    SKU: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    shipping_weight: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    sales: Optional[int] = None
    views: Optional[int] = None
    featured: Optional[bool] = None
    new_arrival: Optional[bool] = None
    best_seller: Optional[bool] = None
    published: Optional[bool] = None

class Product(ProductBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserRegister(BaseModel):
    name: str
    email: str
    phone: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserDevLogin(BaseModel):
    phone: str

class UserOut(BaseModel):
    id: str
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class CartItemInput(BaseModel):
    product_id: str
    quantity: int

class CartMergeInput(BaseModel):
    items: List[CartItemInput]

class UserOTPSend(BaseModel):
    phone: str
    name: str

class UserOTPVerify(BaseModel):
    phone: str
    otp: str

import html

def sanitize_string(val: Optional[str]) -> Optional[str]:
    if val is None or not isinstance(val, str):
        return val
    return html.escape(val.strip())

class OrderItemInput(BaseModel):
    product_id: Optional[str] = None
    title: str
    price: float
    thumbnail: Optional[str] = None

    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, v):
        return sanitize_string(v)

class OrderCreateInput(BaseModel):
    order_id: str
    name: str
    email: Optional[str] = None
    phone: str
    address: str
    payment_method: str = "upi"
    items: List[OrderItemInput]
    grand_total: float
    status: str = "Processing"
    payment_status: str = "pending"
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    failure_reason: Optional[str] = None

    @field_validator('name', 'address', 'email', 'order_id', mode='before')
    @classmethod
    def sanitize_order_fields(cls, v):
        return sanitize_string(v)

class PaymentOrderCreateInput(BaseModel):
    amount: float
    receipt: Optional[str] = None

class PaymentVerifyInput(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentLinkCreateInput(BaseModel):
    amount: float
    receipt: str
    name: str
    email: str
    phone: str
    callback_url: str
    address: Optional[str] = None
    items: Optional[List[OrderItemInput]] = None

class PaymentLinkVerifyInput(BaseModel):
    razorpay_payment_id: str
    razorpay_payment_link_id: str
    razorpay_payment_link_reference_id: str
    razorpay_payment_link_status: str
    razorpay_signature: str


class OrderStatusUpdateInput(BaseModel):
    status: str
    notify_whatsapp: bool = False

class AdminLoginInput(BaseModel):
    login_id: str
    password: str

class StoreSettings(BaseModel):
    delivery_charge_threshold: int
    delivery_charge: int
    cod_enabled: bool




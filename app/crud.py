from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import ProductCreate, ProductUpdate, StoreSettings
from app.database import get_database

def helper_product(product) -> dict:
    if not product:
        return {}
    product["_id"] = str(product["_id"])
    return product

async def get_products(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    featured: Optional[bool] = None,
    new_arrival: Optional[bool] = None,
    best_seller: Optional[bool] = None,
    published_only: bool = True,
    search: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[dict]:
    db = get_database()
    query: Dict[str, Any] = {}

    if published_only:
        query["published"] = True
    
    if category:
        query["category"] = category
        
    if tag:
        query["tags"] = tag

    if featured is not None:
        query["featured"] = featured

    if new_arrival is not None:
        query["new_arrival"] = new_arrival

    if best_seller is not None:
        query["best_seller"] = best_seller

    if search:
        # Simple case-insensitive search on title and description
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"short_description": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.products.find(query).skip(skip).limit(limit)
    products = []
    async for product in cursor:
        products.append(helper_product(product))
    return products

async def get_product_by_id(product_id: str) -> Optional[dict]:
    db = get_database()
    if not ObjectId.is_valid(product_id):
        return None
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    return helper_product(product) if product else None

async def get_product_by_slug(slug: str) -> Optional[dict]:
    db = get_database()
    product = await db.products.find_one({"slug": slug})
    return helper_product(product) if product else None

async def create_product(product_data: ProductCreate) -> dict:
    db = get_database()
    product_dict = product_data.model_dump()
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    
    # Check if slug already exists to prevent duplication
    existing = await db.products.find_one({"slug": product_data.slug})
    if existing:
        # Modify slug slightly to ensure uniqueness if needed, or raise exception
        pass
        
    result = await db.products.insert_one(product_dict)
    new_product = await db.products.find_one({"_id": result.inserted_id})
    return helper_product(new_product)

async def update_product(product_id: str, product_data: ProductUpdate) -> Optional[dict]:
    db = get_database()
    if not ObjectId.is_valid(product_id):
        return None
        
    update_dict = {k: v for k, v in product_data.model_dump(exclude_unset=True).items()}
    if not update_dict:
        return await get_product_by_id(product_id)
        
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_dict}
    )
    return await get_product_by_id(product_id)

async def delete_product(product_id: str) -> bool:
    db = get_database()
    if not ObjectId.is_valid(product_id):
        return False
    result = await db.products.delete_one({"_id": ObjectId(product_id)})
    return result.deleted_count > 0

import uuid
from app.models import UserRegister

async def get_user_by_email(email: str) -> Optional[dict]:
    db = get_database()
    user = await db.users.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def get_user_by_phone(phone: str) -> Optional[dict]:
    db = get_database()
    user = await db.users.find_one({"phone": phone})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def dev_login_or_register(phone: str, name: Optional[str] = None) -> dict:
    db = get_database()
    user = await get_user_by_phone(phone)
    if not user:
        user_dict = {
            "phone": phone,
            "created_at": datetime.utcnow()
        }
        if name:
            user_dict["name"] = name
        result = await db.users.insert_one(user_dict)
        user = await db.users.find_one({"_id": result.inserted_id})
        user["_id"] = str(user["_id"])
    elif name and not user.get("name"):
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"name": name}})
        user["name"] = name
    return user

async def update_user_profile(user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> Optional[dict]:
    db = get_database()
    if not ObjectId.is_valid(user_id):
        return None
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if email is not None:
        update_data["email"] = email

    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def register_user(user_data: UserRegister) -> Optional[dict]:
    db = get_database()
    existing = await get_user_by_email(user_data.email)
    if existing:
        return None
    user_dict = user_data.model_dump()
    user_dict["created_at"] = datetime.utcnow()
    result = await db.users.insert_one(user_dict)
    new_user = await db.users.find_one({"_id": result.inserted_id})
    new_user["_id"] = str(new_user["_id"])
    return new_user

async def authenticate_user(email: str, password: str) -> Optional[dict]:
    db = get_database()
    user = await db.users.find_one({"email": email, "password": password})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def create_session(user_id: str) -> str:
    db = get_database()
    token = uuid.uuid4().hex
    session_doc = {
        "token": token,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }
    await db.sessions.insert_one(session_doc)
    return token

async def get_user_by_session(token: str) -> Optional[dict]:
    db = get_database()
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def get_cart(user_id: str) -> List[dict]:
    db = get_database()
    cart_doc = await db.carts.find_one({"user_id": user_id})
    if not cart_doc:
        return []
    return cart_doc.get("items", [])

async def update_cart(user_id: str, items: List[dict]) -> List[dict]:
    db = get_database()
    # Clean items to ensure they contain product_id and quantity
    cleaned_items = []
    for item in items:
        cleaned_items.append({
            "product_id": str(item["product_id"]),
            "quantity": int(item["quantity"])
        })
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": cleaned_items, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return cleaned_items

async def merge_carts(user_id: str, guest_items: List[dict]) -> List[dict]:
    db = get_database()
    current_items = await get_cart(user_id)
    
    # Merge logic
    merged = {item["product_id"]: item["quantity"] for item in current_items}
    for g_item in guest_items:
        g_pid = str(g_item["product_id"])
        g_qty = int(g_item["quantity"])
        if g_pid in merged:
            merged[g_pid] += g_qty # Combine quantities
        else:
            merged[g_pid] = g_qty
            
    items_list = [{"product_id": pid, "quantity": qty} for pid, qty in merged.items()]
    return await update_cart(user_id, items_list)

async def get_wishlist(user_id: str) -> List[str]:
    db = get_database()
    wl_doc = await db.wishlists.find_one({"user_id": user_id})
    if not wl_doc:
        return []
    return wl_doc.get("product_ids", [])

async def add_to_wishlist(user_id: str, product_id: str) -> List[str]:
    db = get_database()
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$addToSet": {"product_ids": product_id}, "$set": {"updated_at": datetime.utcnow()}},
        upsert=True
    )
    return await get_wishlist(user_id)

async def remove_from_wishlist(user_id: str, product_id: str) -> List[str]:
    db = get_database()
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$pull": {"product_ids": product_id}, "$set": {"updated_at": datetime.utcnow()}},
        upsert=True
    )
    return await get_wishlist(user_id)

from app.models import OrderCreateInput

def helper_order(order) -> dict:
    if not order:
        return {}
    order["_id"] = str(order["_id"])
    return order

async def create_order(user_id: str, order_data: OrderCreateInput) -> dict:
    db = get_database()
    order_dict = order_data.model_dump()
    order_dict["user_id"] = user_id

    # Check if order with this order_id already exists (pre-created pending order)
    existing = await db.orders.find_one({"order_id": order_data.order_id})
    if existing:
        update_fields = {k: v for k, v in order_dict.items() if k not in ("_id", "created_at")}
        # Preserve status if it was already updated to Processing or Paid by webhook!
        if existing.get("status") in ("Processing", "Paid", "Confirmed"):
            update_fields["status"] = existing.get("status")
        if existing.get("payment_status") == "paid":
            update_fields["payment_status"] = "paid"
            
        update_fields["updated_at"] = datetime.utcnow()
        await db.orders.update_one({"_id": existing["_id"]}, {"$set": update_fields})
        updated = await db.orders.find_one({"_id": existing["_id"]})
        return helper_order(updated)

    order_dict["created_at"] = datetime.utcnow()
    result = await db.orders.insert_one(order_dict)
    new_order = await db.orders.find_one({"_id": result.inserted_id})
    return helper_order(new_order)

async def get_user_orders(user_id: str) -> List[dict]:
    db = get_database()
    cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1)
    orders = []
    async for order in cursor:
        orders.append(helper_order(order))
    return orders

async def get_all_orders() -> List[dict]:
    db = get_database()
    cursor = db.orders.find({}).sort("created_at", -1)
    orders = []
    async for order in cursor:
        orders.append(helper_order(order))
    return orders

async def get_order_by_identifier(identifier: str) -> Optional[dict]:
    db = get_database()
    query = {
        "$or": [
            {"order_id": identifier},
            {"razorpay_order_id": identifier},
            {"receipt": identifier}
        ]
    }
    if ObjectId.is_valid(identifier):
        query["$or"].append({"_id": ObjectId(identifier)})
        
    order = await db.orders.find_one(query)
    return helper_order(order) if order else None

async def update_order_payment_status(
    identifier: str,
    payment_status: str,
    order_status: str,
    razorpay_payment_id: Optional[str] = None,
    razorpay_order_id: Optional[str] = None,
    failure_reason: Optional[str] = None
) -> Optional[dict]:
    db = get_database()
    order = await get_order_by_identifier(identifier)
    if not order:
        return None

    update_fields = {
        "payment_status": payment_status,
        "status": order_status,
        "updated_at": datetime.utcnow()
    }
    if razorpay_payment_id:
        update_fields["razorpay_payment_id"] = razorpay_payment_id
    if razorpay_order_id:
        update_fields["razorpay_order_id"] = razorpay_order_id
    if failure_reason:
        update_fields["failure_reason"] = failure_reason

    await db.orders.update_one(
        {"_id": ObjectId(order["_id"])},
        {"$set": update_fields}
    )
    updated = await db.orders.find_one({"_id": ObjectId(order["_id"])})
    return helper_order(updated) if updated else None

async def update_order_status_by_admin(order_id: str, new_status: str, notify_whatsapp: bool = False) -> Optional[dict]:
    db = get_database()
    order = await get_order_by_identifier(order_id)
    if not order:
        return None

    update_fields = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }

    if new_status in ("Paid", "Processing", "Dispatched", "Shipped", "Delivered", "Confirmed"):
        if order.get("payment_status") != "paid":
            update_fields["payment_status"] = "paid"

    await db.orders.update_one(
        {"_id": ObjectId(order["_id"])},
        {"$set": update_fields}
    )
    updated = await db.orders.find_one({"_id": ObjectId(order["_id"])})
    return helper_order(updated) if updated else None

async def get_store_settings() -> dict:
    db = get_database()
    settings_doc = await db.settings.find_one({})
    if not settings_doc:
        default_settings = {
            "delivery_charge_threshold": 999,
            "delivery_charge": 99,
            "cod_enabled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.settings.insert_one(default_settings)
        default_settings["_id"] = str(result.inserted_id)
        return default_settings
    
    settings_doc["_id"] = str(settings_doc["_id"])
    return settings_doc


async def update_store_settings(settings_data: StoreSettings) -> dict:
    db = get_database()
    update_dict = settings_data.model_dump()
    update_dict["updated_at"] = datetime.utcnow()
    await db.settings.update_one(
        {},
        {"$set": update_dict},
        upsert=True
    )
    return await get_store_settings()


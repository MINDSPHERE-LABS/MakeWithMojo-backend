from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import ProductCreate, ProductUpdate
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

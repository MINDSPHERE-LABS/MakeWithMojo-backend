from fastapi import FastAPI, HTTPException, status, Query, File, UploadFile, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import shutil
from pydantic import BaseModel

from app.database import connect_to_mongo, close_mongo_connection
from app.models import (
    Product, ProductCreate, ProductUpdate,
    UserRegister, UserLogin, UserOut, CartItemInput, CartMergeInput, UserDevLogin,
    UserOTPSend, UserOTPVerify, OrderCreateInput, UserProfileUpdate,
    PaymentOrderCreateInput, PaymentVerifyInput,
    PaymentLinkCreateInput, PaymentLinkVerifyInput,
    OrderStatusUpdateInput, AdminLoginInput,
    StoreSettings
)
from app import crud
from app.auth.routes import router as auth_router
from app.services.razorpay_service import razorpay_service
from app.auth.rate_limiter import rate_limiter, get_client_ip

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB and seed initial admin user
    await connect_to_mongo()
    await crud.seed_initial_admin_user()
    yield
    # Shutdown: Close Connection
    await close_mongo_connection()

app = FastAPI(
    title="MakeWithMojo API",
    description="Backend API for MakeWithMojo 3D Printed Products Storefront",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import FileResponse, Response

# Environment-agnostic images directory routing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_IMAGES_DIR = r"C:\Users\Vaibhav\Desktop\MakeWithMojo\MakeWithMojo-frontend\public\images"

if os.path.exists(LOCAL_IMAGES_DIR):
    IMAGES_DIR = LOCAL_IMAGES_DIR
    UPLOAD_DIR = os.path.join(LOCAL_IMAGES_DIR, "products")
else:
    IMAGES_DIR = os.path.join(BASE_DIR, "public", "images")
    UPLOAD_DIR = os.path.join(IMAGES_DIR, "products")

# Ensure the upload directories are created on launch
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/images/products/{filename:path}")
async def get_product_image_with_fallback(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # Fallback to RABBIT.jpeg or available product image if file is missing
    fallback_rabbit = os.path.join(UPLOAD_DIR, "RABBIT.jpeg")
    if os.path.exists(fallback_rabbit):
        return FileResponse(fallback_rabbit)

    try:
        existing_files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if existing_files:
            return FileResponse(os.path.join(UPLOAD_DIR, existing_files[0]))
    except Exception:
        pass

    svg_fallback = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="#f3f4f6"/><path d="M150 250 L200 180 L250 250 Z" fill="#d1d5db"/><circle cx="160" cy="160" r="20" fill="#d1d5db"/><text x="200" y="300" font-size="16" font-weight="bold" font-family="sans-serif" fill="#9ca3af" text-anchor="middle">3D Creation Model</text></svg>"""
    return Response(content=svg_fallback, media_type="image/svg+xml")

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

app.include_router(auth_router)

@app.api_route("/health", methods=["GET", "HEAD", "POST", "OPTIONS"])
async def health_check():
    return {"status": "healthy", "service": "MakeWithMojo-backend"}

# --- Authentication Dependencies ---
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "makewithmojo_admin_secret_key_2026")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
    token = authorization.split(" ")[1]
    user = await crud.get_user_by_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid"
        )
    return user

async def get_current_admin_user(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None)
):
    if x_admin_key and x_admin_key == ADMIN_SECRET_KEY:
        return {"_id": "admin_system", "role": "admin", "name": "System Admin"}

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user = await crud.get_user_by_session(token)
        if user and user.get("role") == "admin":
            return user
        if user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to perform this action"
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid admin authorization credentials"
    )

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), current_admin: dict = Depends(get_current_admin_user)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/images/products/{file.filename}"}

@app.get("/api/products", response_model=List[Product])
async def list_products(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    featured: Optional[bool] = None,
    new_arrival: Optional[bool] = None,
    best_seller: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0)
):
    products = await crud.get_products(
        category=category,
        tag=tag,
        featured=featured,
        new_arrival=new_arrival,
        best_seller=best_seller,
        search=search,
        limit=limit,
        skip=skip
    )
    return products

@app.get("/api/products/slug/{slug}", response_model=Product)
async def get_product_by_slug(slug: str):
    product = await crud.get_product_by_slug(slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found"
        )
    return product
@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await crud.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found"
        )
    return product

@app.post("/api/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def upload_product(product: ProductCreate, current_admin: dict = Depends(get_current_admin_user)):
    # Check if product slug exists
    existing = await crud.get_product_by_slug(product.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{product.slug}' already exists."
        )
    new_product = await crud.create_product(product)
    return new_product

@app.put("/api/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductUpdate, current_admin: dict = Depends(get_current_admin_user)):
    product = await crud.update_product(product_id, product_update)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found or invalid format"
        )
    return product

@app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, current_admin: dict = Depends(get_current_admin_user)):
    success = await crud.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found or invalid format"
        )
    return

# --- Auth Routes ---
@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    user = await crud.register_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    token = await crud.create_session(user["_id"])
    return {"token": token, "user": user}

@app.post("/api/auth/login")
async def login(credentials: UserLogin, request: Request):
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        identifier=f"user_login:{client_ip}",
        max_requests=5,
        window_seconds=120,
        custom_message="Too many login attempts. Please wait 2 minutes (120 seconds)."
    )
    user = await crud.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    token = await crud.create_session(user["_id"])
    return {"token": token, "user": user}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.put("/api/auth/me")
async def update_me(payload: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    updated_user = await crud.update_user_profile(current_user["_id"], payload.name, payload.email)
    return updated_user

@app.post("/api/auth/dev-login")
async def dev_login(credentials: UserDevLogin):
    user = await crud.dev_login_or_register(credentials.phone)
    token = await crud.create_session(user["_id"])
    return {"token": token, "user": user}

# --- OTP Verification Routers ---
import random
from datetime import datetime, timedelta

# In-memory OTP database mapping phone numbers to OTP verification records
otp_store = {}

@app.post("/api/auth/otp/send")
async def send_otp(payload: UserOTPSend, request: Request):
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        identifier=f"otp_send:{client_ip}:{payload.phone}",
        max_requests=3,
        window_seconds=120,
        custom_message="Too many OTP requests for this number. Please wait 2 minutes (120 seconds)."
    )

    otp = str(random.randint(100000, 999999))
    otp_store[payload.phone] = {
        "otp": otp,
        "name": payload.name,
        "expires_at": datetime.utcnow() + timedelta(minutes=2)
    }
    
    # Dev mode OTP console printout
    print(f"\n==================================================")
    print(f"[OTP DEV SERVICE] Mobile verification code for {payload.phone}:")
    print(f"CODE: {otp}")
    print(f"==================================================\n")
    
    return {"message": "OTP sent successfully", "phone": payload.phone, "otp": otp}

@app.post("/api/auth/otp/verify")
async def verify_otp(payload: UserOTPVerify, request: Request):
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        identifier=f"otp_verify:{client_ip}:{payload.phone}",
        max_requests=5,
        window_seconds=120,
        custom_message="Too many OTP verification attempts. Please wait 2 minutes (120 seconds)."
    )

    entry = otp_store.get(payload.phone)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP sent to this mobile number"
        )
    if entry["expires_at"] < datetime.utcnow():
        otp_store.pop(payload.phone, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired"
        )
    if entry["otp"] != payload.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP code"
        )
    
    user = await crud.dev_login_or_register(payload.phone, entry["name"])
    token = await crud.create_session(user["_id"])
    
    # Clear OTP cache after validation
    otp_store.pop(payload.phone, None)
    
    return {"token": token, "user": user}

# --- Cart Routes ---
@app.get("/api/cart")
async def retrieve_cart(current_user: dict = Depends(get_current_user)):
    items = await crud.get_cart(current_user["_id"])
    return items

@app.post("/api/cart")
async def sync_cart(items: List[CartItemInput], current_user: dict = Depends(get_current_user)):
    items_dict = [item.model_dump() for item in items]
    result = await crud.update_cart(current_user["_id"], items_dict)
    return result

@app.post("/api/cart/merge")
async def merge_guest_cart(payload: CartMergeInput, current_user: dict = Depends(get_current_user)):
    guest_items_dict = [item.model_dump() for item in payload.items]
    result = await crud.merge_carts(current_user["_id"], guest_items_dict)
    return result

# --- Wishlist Routes ---
class WishlistAddInput(BaseModel):
    product_id: str

@app.get("/api/wishlist")
async def retrieve_wishlist(current_user: dict = Depends(get_current_user)):
    product_ids = await crud.get_wishlist(current_user["_id"])
    return product_ids

@app.post("/api/wishlist")
async def add_wishlist_item(payload: WishlistAddInput, current_user: dict = Depends(get_current_user)):
    result = await crud.add_to_wishlist(current_user["_id"], payload.product_id)
    return result

@app.delete("/api/wishlist/{product_id}")
async def delete_wishlist_item(product_id: str, current_user: dict = Depends(get_current_user)):
    result = await crud.remove_from_wishlist(current_user["_id"], product_id)
    return result

# --- Checkout Validation ---
@app.get("/api/checkout/validate")
async def validate_checkout(current_user: dict = Depends(get_current_user)):
    return {"authenticated": True, "user_id": current_user["_id"]}

# --- Razorpay Payment Routes ---
@app.get("/api/payment/config")
async def get_payment_config():
    return {
        "key_id": razorpay_service.key_id or "rzp_test_MWM12345",
        "is_configured": razorpay_service.is_configured()
    }

@app.post("/api/payment/create-order")
async def create_razorpay_order(payload: PaymentOrderCreateInput, current_user: dict = Depends(get_current_user)):
    receipt_id = payload.receipt or f"rcpt_{int(datetime.utcnow().timestamp())}"
    res = await razorpay_service.create_razorpay_order(payload.amount, receipt_id)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to create Razorpay payment order")
        )
    return res

@app.post("/api/payment/verify")
async def verify_razorpay_payment(payload: PaymentVerifyInput, current_user: dict = Depends(get_current_user)):
    valid = razorpay_service.verify_payment_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay payment signature verification failed"
        )
    return {"success": True, "message": "Razorpay payment verified successfully"}

@app.post("/api/payment/create-link")
async def create_payment_link_endpoint(payload: PaymentLinkCreateInput, current_user: dict = Depends(get_current_user)):
    # Pre-create pending order in DB so webhook can find it instantly when payment completes
    existing_order = await crud.get_order_by_identifier(payload.receipt)
    if not existing_order:
        try:
            pending_data = OrderCreateInput(
                order_id=payload.receipt,
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                address=payload.address or "Pending Delivery Address",
                payment_method="Razorpay Hosted Redirect",
                items=payload.items or [],
                grand_total=payload.amount,
                status="Pending Payment",
                payment_status="pending"
            )
            await crud.create_order(current_user["_id"], pending_data)
            print(f"[PAYMENT LINK] Pre-created pending order in DB: {payload.receipt}")
        except Exception as e:
            print(f"[PAYMENT LINK] Warning pre-creating order in DB: {e}")

    res = await razorpay_service.create_payment_link(
        payload.amount,
        payload.receipt,
        payload.name,
        payload.email,
        payload.phone,
        payload.callback_url
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to create Razorpay hosted payment link")
        )

    # Save payment short_url on order document so user can resume payment anytime from Order History
    try:
        await crud.update_order_payment_link_info(
            order_id=payload.receipt,
            short_url=res.get("short_url"),
            razorpay_order_id=res.get("plink_id")
        )
    except Exception as e:
        print(f"[PAYMENT LINK] Warning saving short_url on order: {e}")

    return res

@app.post("/api/payment/verify-link")
async def verify_payment_link_endpoint(payload: PaymentLinkVerifyInput, current_user: dict = Depends(get_current_user)):
    valid = razorpay_service.verify_payment_link_signature(
        payload.razorpay_payment_link_id,
        payload.razorpay_payment_link_reference_id,
        payload.razorpay_payment_link_status,
        payload.razorpay_payment_id,
        payload.razorpay_signature
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay payment link signature verification failed"
        )

    if payload.razorpay_payment_link_status == "paid":
        await crud.update_order_payment_status(
            identifier=payload.razorpay_payment_link_reference_id,
            payment_status="paid",
            order_status="Processing",
            razorpay_payment_id=payload.razorpay_payment_id
        )

    return {"success": True, "message": "Razorpay payment link signature verified successfully"}

@app.post("/api/payment/webhook")
async def razorpay_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    is_valid = razorpay_service.verify_webhook_signature(raw_body, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature"
        )

    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload in webhook request"
        )

    event_type = event_data.get("event")
    payload = event_data.get("payload", {})

    print(f"\n==================================================")
    print(f"[RAZORPAY WEBHOOK] Received event: {event_type}")
    print(f"==================================================\n")

    if event_type in ("payment.captured", "order.paid"):
        payment_entity = payload.get("payment", {}).get("entity", {})
        order_entity = payload.get("order", {}).get("entity", {})

        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id") or order_entity.get("id")
        notes = payment_entity.get("notes", {}) or order_entity.get("notes", {})
        order_id_note = notes.get("order_id") or notes.get("receipt")
        receipt = payment_entity.get("receipt") or order_entity.get("receipt")

        candidates = [c for c in [order_id_note, receipt, razorpay_order_id] if c]

        updated_order = None
        for candidate in candidates:
            updated_order = await crud.update_order_payment_status(
                identifier=candidate,
                payment_status="paid",
                order_status="Processing",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id
            )
            if updated_order:
                print(f"[RAZORPAY WEBHOOK] Order successfully marked as PAID for identifier: {candidate}")
                break

        if not updated_order:
            print(f"[RAZORPAY WEBHOOK] Warning: Order not found for identifiers: {candidates}")

    elif event_type == "payment.failed":
        payment_entity = payload.get("payment", {}).get("entity", {})
        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")
        error_description = payment_entity.get("error_description", "Payment transaction failed")
        error_reason = payment_entity.get("error_reason") or payment_entity.get("error_code")
        notes = payment_entity.get("notes", {})
        order_id_note = notes.get("order_id") or notes.get("receipt")
        receipt = payment_entity.get("receipt")

        candidates = [c for c in [order_id_note, receipt, razorpay_order_id] if c]

        updated_order = None
        for candidate in candidates:
            updated_order = await crud.update_order_payment_status(
                identifier=candidate,
                payment_status="failed",
                order_status="Payment Failed",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                failure_reason=f"{error_description} ({error_reason})" if error_reason else error_description
            )
            if updated_order:
                print(f"[RAZORPAY WEBHOOK] Order marked as FAILED for identifier: {candidate}")
                break

        if not updated_order:
            print(f"[RAZORPAY WEBHOOK] Warning: Order not found for identifiers: {candidates}")

    elif event_type == "payment_link.paid":
        link_entity = payload.get("payment_link", {}).get("entity", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        reference_id = link_entity.get("reference_id")
        razorpay_payment_id = payment_entity.get("id") or link_entity.get("payment_id")

        if reference_id:
            updated_order = await crud.update_order_payment_status(
                identifier=reference_id,
                payment_status="paid",
                order_status="Processing",
                razorpay_payment_id=razorpay_payment_id
            )
            if updated_order:
                print(f"[RAZORPAY WEBHOOK] Payment Link Order marked as PAID for ref: {reference_id}")

    elif event_type in ("payment_link.cancelled", "payment_link.expired"):
        link_entity = payload.get("payment_link", {}).get("entity", {})
        reference_id = link_entity.get("reference_id")
        if reference_id:
            await crud.update_order_payment_status(
                identifier=reference_id,
                payment_status="failed",
                order_status="Payment Cancelled",
                failure_reason=f"Payment link {event_type.split('.')[1]}"
            )

    return {"status": "ok", "event": event_type}

# --- Order Routes ---
@app.post("/api/orders")
async def create_new_order(payload: OrderCreateInput, current_user: dict = Depends(get_current_user)):
    order = await crud.create_order(current_user["_id"], payload)
    return order

@app.get("/api/orders")
async def get_my_orders(current_user: dict = Depends(get_current_user)):
    orders = await crud.get_user_orders(current_user["_id"])
    return orders

# --- Admin Authentication Routes ---
@app.post("/api/admin/login")
async def admin_login_endpoint(payload: AdminLoginInput, request: Request):
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        identifier=f"admin_login:{client_ip}",
        max_requests=5,
        window_seconds=120,
        custom_message="Too many admin login attempts. Please wait 2 minutes (120 seconds)."
    )
    user = await crud.authenticate_admin_user(payload.login_id, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials or unauthorized account."
        )
    token = await crud.create_session(user["_id"])
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["_id"],
            "name": user.get("name", "Admin"),
            "email": user.get("email"),
            "role": user.get("role", "admin")
        }
    }

@app.get("/api/admin/me")
async def get_admin_me(current_admin: dict = Depends(get_current_admin_user)):
    return {
        "authenticated": True,
        "admin": {
            "id": current_admin.get("_id"),
            "name": current_admin.get("name", "Admin"),
            "email": current_admin.get("email"),
            "role": current_admin.get("role", "admin")
        }
    }

@app.get("/api/admin/orders")
async def get_admin_orders(current_admin: dict = Depends(get_current_admin_user)):
    orders = await crud.get_all_orders()
    return orders

@app.put("/api/admin/orders/{order_id}/status")
async def update_admin_order_status(order_id: str, payload: OrderStatusUpdateInput, current_admin: dict = Depends(get_current_admin_user)):
    updated = await crud.update_order_status_by_admin(
        order_id=order_id,
        new_status=payload.status,
        notify_whatsapp=payload.notify_whatsapp
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found"
        )

    if payload.notify_whatsapp:
        print(f"\n==================================================")
        print(f"[WHATSAPP NOTIFICATION HOOK] (Disabled) Would send WhatsApp status alert for order {order_id} -> '{payload.status}'")
        print(f"==================================================\n")

    return {"success": True, "order": updated}


@app.get("/api/settings")
async def get_settings():
    settings = await crud.get_store_settings()
    return settings


@app.put("/api/settings")
async def update_settings(settings_data: StoreSettings, current_admin: dict = Depends(get_current_admin_user)):
    settings = await crud.update_store_settings(settings_data)
    return settings



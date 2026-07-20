import urllib.request
import json

def upload_product():
    url = "http://localhost:8000/api/products"
    
    product_data = {
        "title": "PolyGlow Geometric Planter",
        "slug": "polyglow-geometric-planter",
        "short_description": "Stunning geometric self-watering planter printed in translucent glow-in-the-dark polymer.",
        "description": "The PolyGlow Geometric Planter integrates state-of-the-art organic structural design with a self-watering reservoir. Printed in custom-engineered luminescent PLA, it charges under sunlight or LED desk lamps, casting a beautiful, soft ambient glow at night. The modular design features a separate drainage tray that snaps into the geometric base, maintaining clean, modern lines while keeping your plant healthy.",
        "price": 1299.00,
        "discount_price": 999.00,
        "category": "Planters",
        "subcategory": "Home Décor",
        "tags": ["decor", "minimalist", "planter", "glow-in-the-dark"],
        "thumbnail": "/images/products/geometric_vase.jpg", # Reuses existing image assets
        "gallery": [
            "/images/products/geometric_vase.jpg"
        ],
        "videos": [],
        "available_colors": ["Luminescent Green", "Ghost Blue"],
        "available_sizes": ["Medium (12cm)"],
        "material": "Glow PLA+",
        "print_quality": "0.16mm Fine",
        "production_time": "1-2 Days",
        "stock": 35,
        "SKU": "MWM-PL-009",
        "weight": 190.0,
        "dimensions": "12x12x11 cm",
        "shipping_weight": 300.0,
        "rating": 5.0,
        "review_count": 5,
        "sales": 18,
        "views": 75,
        "featured": True,
        "new_arrival": True,
        "best_seller": False,
        "published": True
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(product_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_data = json.loads(res_body)
            print("Success! Test Product uploaded to MakeWithMojo backend.")
            print(f"Product ID: {res_data.get('id')}")
            print(f"Product Title: {res_data.get('title')}")
            print(f"Slug: {res_data.get('slug')}")
            print(f"Featured: {res_data.get('featured')}")
            print("This product will immediately render on the live website homepage without rebuild/restart!")
    except Exception as e:
        print(f"Error uploading product: {e}")

if __name__ == "__main__":
    upload_product()

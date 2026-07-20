import asyncio
from datetime import datetime
from app.database import connect_to_mongo, get_database, close_mongo_connection

products_seed = [
    {
        "title": "Apex Cyberpunk Headphone Stand",
        "slug": "apex-cyberpunk-headphone-stand",
        "short_description": "Futuristic cyberpunk-themed headphone hanger with customizable LED routing and matte finish.",
        "description": "Elevate your gaming setup with the Apex Cyberpunk Headphone Stand. Modeled after futuristic urban aesthetics, this stand is printed with high-density premium PLA+ for maximum durability. It features structured wire routing grooves, non-slip silicone feet channels, and a headrest design that fits all major headphones without putting tension on the headband. Perfect for gamers, creators, and audio professionals who want to make a bold statement.",
        "price": 2499.00,
        "discount_price": 1999.00,
        "category": "Headphone Stands",
        "subcategory": "Gaming Accessories",
        "tags": ["gaming", "desk-setup", "cyberpunk", "led-ready"],
        "thumbnail": "/images/products/cyberpunk_stand.jpg",
        "gallery": [
            "/images/products/cyberpunk_stand.jpg",
            "/images/products/cyberpunk_stand_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Matte Black", "Gunmetal Grey", "Neon Orange", "Acid Green"],
        "available_sizes": ["Standard"],
        "material": "Premium PLA+",
        "print_quality": "0.12mm Extra Fine",
        "production_time": "2-3 Days",
        "stock": 25,
        "SKU": "MWM-HS-001",
        "weight": 420.0,
        "dimensions": "15x12x28 cm",
        "shipping_weight": 550.0,
        "rating": 4.8,
        "review_count": 14,
        "sales": 87,
        "views": 320,
        "featured": True,
        "new_arrival": False,
        "best_seller": True,
        "published": True
    },
    {
        "title": "Geometric Faceted Ceramic-Style Vase",
        "slug": "geometric-faceted-ceramic-style-vase",
        "short_description": "Minimalist geometric origami vase featuring silk-gloss finishes and watertight construction.",
        "description": "Bring modern sculpture into your living space. This geometric faceted vase is printed using state-of-the-art spiral vase printing techniques, creating a seamless piece without visible layer lines. Made from premium silk-sheen polymer, it reflects light elegantly from every angle. It includes an internal glass insert to guarantee 100% water-proofing for fresh bouquets, or it can be used standalone with dried flora.",
        "price": 1499.00,
        "discount_price": None,
        "category": "Vases",
        "subcategory": "Home Décor",
        "tags": ["decor", "minimalist", "vase", "ceramic-style"],
        "thumbnail": "/images/products/geometric_vase.jpg",
        "gallery": [
            "/images/products/geometric_vase.jpg",
            "/images/products/geometric_vase_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Pearl White", "Champagne Gold", "Emerald Green", "Blush Pink"],
        "available_sizes": ["Small (15cm)", "Medium (20cm)", "Large (25cm)"],
        "material": "Silk PLA",
        "print_quality": "0.16mm Fine",
        "production_time": "1-2 Days",
        "stock": 40,
        "SKU": "MWM-VS-002",
        "weight": 210.0,
        "dimensions": "10x10x20 cm",
        "shipping_weight": 350.0,
        "rating": 4.9,
        "review_count": 22,
        "sales": 115,
        "views": 412,
        "featured": True,
        "new_arrival": True,
        "best_seller": False,
        "published": True
    },
    {
        "title": "Modular Magnetic Desk Organizer",
        "slug": "modular-magnetic-desk-organizer",
        "short_description": "High-utility 4-piece desk organizer tray with integrated Neodymium magnets.",
        "description": "De-clutter your creative zone with the MakeWithMojo Modular Desk Organizer. This set features four separate magnetic modules: a pen holder tray, a phone dock with charging cable pass-through, a paperclip dish, and a sticky note holder. Embedded rare-earth magnets ensure modules snap together in any configuration you prefer. Finished with rubberized bottom pads to prevent sliding on wood, metal, or glass desk surfaces.",
        "price": 2299.00,
        "discount_price": 1799.00,
        "category": "Organizers",
        "subcategory": "Desk Accessories",
        "tags": ["office", "organizer", "modular", "magnetic"],
        "thumbnail": "/images/products/desk_organizer.jpg",
        "gallery": [
            "/images/products/desk_organizer.jpg",
            "/images/products/desk_organizer_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Carbon Fiber Black", "Stone Grey", "Marble White"],
        "available_sizes": ["One Size"],
        "material": "PETG / Neodymium Magnets",
        "print_quality": "0.20mm Standard",
        "production_time": "2 Days",
        "stock": 15,
        "SKU": "MWM-DO-003",
        "weight": 350.0,
        "dimensions": "24x8x6 cm",
        "shipping_weight": 480.0,
        "rating": 4.6,
        "review_count": 9,
        "sales": 43,
        "views": 189,
        "featured": False,
        "new_arrival": False,
        "best_seller": False,
        "published": True
    },
    {
        "title": "Aero Breathable Planter Pot",
        "slug": "aero-breathable-planter-pot",
        "short_description": "Architectural self-draining planter pot with double-wall aeration channels.",
        "description": "Give your houseplants the root health they deserve. The Aero Breathable Planter is engineered with a double-wall structure that allows continuous airflow directly to the soil, preventing root rot and waterlogging. The hidden integrated drip tray snaps onto the bottom, maintaining clean lines while catching excess moisture. The modern architectural lattice design complements monsteras, snake plants, and succulents alike.",
        "price": 1199.00,
        "discount_price": None,
        "category": "Planters",
        "subcategory": "Home Décor",
        "tags": ["plants", "planter", "interior-design", "functional"],
        "thumbnail": "/images/products/aero_planter.jpg",
        "gallery": [
            "/images/products/aero_planter.jpg",
            "/images/products/aero_planter_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Matte Terrazzo", "Sage Green", "Desert Sand", "Slate Black"],
        "available_sizes": ["4 inch", "6 inch"],
        "material": "Recycled Bio-PLA",
        "print_quality": "0.20mm Standard",
        "production_time": "1-2 Days",
        "stock": 50,
        "SKU": "MWM-PL-004",
        "weight": 180.0,
        "dimensions": "14x14x13 cm",
        "shipping_weight": 280.0,
        "rating": 4.7,
        "review_count": 18,
        "sales": 64,
        "views": 250,
        "featured": False,
        "new_arrival": True,
        "best_seller": False,
        "published": True
    },
    {
        "title": "Cyber Oni Samurai Mask",
        "slug": "cyber-oni-samurai-mask",
        "short_description": "Wearable high-detail Cyberpunk Oni mask, perfect for cosplay, gaming rooms, or wall art.",
        "description": "An imposing fusion of traditional Japanese culture and neon cyberpunk styling. The Cyber Oni Samurai Mask features sharp contours, custom breathing grill work, and adjustable strap mounts. Use it as a jaw-dropping cosplay accessory or mount it on the wall of your gaming den with the included invisible hook hanger. Hand-finished and inspected to ensure every edge is clean and premium.",
        "price": 5999.00,
        "discount_price": 4999.00,
        "category": "Masks",
        "subcategory": "Cosplay",
        "tags": ["cosplay", "samurai", "wall-art", "wearable"],
        "thumbnail": "/images/products/oni_mask.jpg",
        "gallery": [
            "/images/products/oni_mask.jpg",
            "/images/products/oni_mask_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Shadow Black & Crimson Red", "Ghost White & Teal", "Gold & Matte Black"],
        "available_sizes": ["Standard Adult"],
        "material": "High-Impact ABS",
        "print_quality": "0.12mm Extra Fine",
        "production_time": "4-5 Days",
        "stock": 8,
        "SKU": "MWM-MSK-005",
        "weight": 380.0,
        "dimensions": "18x14x22 cm",
        "shipping_weight": 600.0,
        "rating": 5.0,
        "review_count": 31,
        "sales": 58,
        "views": 590,
        "featured": True,
        "new_arrival": False,
        "best_seller": True,
        "published": True
    },
    {
        "title": "Floating Origami Crane Wall Art Set",
        "slug": "floating-origami-crane-wall-art-set",
        "short_description": "Set of 3 minimalist wall-mountable origami flying cranes with hidden keyhole mounts.",
        "description": "Transform a plain wall into an artistic installation. This set of 3 origami-style flying cranes displays a gradient of flight motions. Printed with ultra-light, rigid composite polymer, they mount flush against the wall via hidden keyhole hangers (template and mounting pins included). The sharp, angular geometric folds cast dramatic, evolving shadows throughout the day as your room's lighting changes.",
        "price": 1899.00,
        "discount_price": None,
        "category": "Wall Art",
        "subcategory": "Home Décor",
        "tags": ["wall-art", "decor", "origami", "minimalist"],
        "thumbnail": "/images/products/origami_cranes.jpg",
        "gallery": [
            "/images/products/origami_cranes.jpg",
            "/images/products/origami_cranes_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Matte White", "Matte Black", "Metallic Gold"],
        "available_sizes": ["Standard Set"],
        "material": "Lightweight Matte PLA",
        "print_quality": "0.16mm Fine",
        "production_time": "2 Days",
        "stock": 30,
        "SKU": "MWM-WA-006",
        "weight": 120.0,
        "dimensions": "22x22x2 cm each",
        "shipping_weight": 290.0,
        "rating": 4.7,
        "review_count": 11,
        "sales": 29,
        "views": 150,
        "featured": False,
        "new_arrival": False,
        "best_seller": False,
        "published": True
    },
    {
        "title": "Steampunk Gear Dice Tower",
        "slug": "steampunk-gear-dice-tower",
        "short_description": "Mechanical-themed dice roller with moving gear details and internal spiral stair baffles.",
        "description": "Add theatrical tension to your tabletop RPG nights. The Steampunk Gear Dice Tower channels your dice through a series of internal gears and baffle steps, ensuring completely randomized rolls every time. The dice emerge into a brass-accented catcher tray. Printed with premium bronze-filled filament, then carefully hand-buffed to give it an authentic, metallic sheen with slight weathering details.",
        "price": 2999.00,
        "discount_price": 2499.00,
        "category": "Gaming Accessories",
        "subcategory": "Miniatures",
        "tags": ["gaming", "steampunk", "ttrpg", "dice"],
        "thumbnail": "/images/products/dice_tower.jpg",
        "gallery": [
            "/images/products/dice_tower.jpg",
            "/images/products/dice_tower_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Antique Bronze", "Corroded Copper", "Iron Ore"],
        "available_sizes": ["One Size"],
        "material": "Bronze-Filled Composite PLA",
        "print_quality": "0.16mm Fine",
        "production_time": "3 Days",
        "stock": 12,
        "SKU": "MWM-GA-007",
        "weight": 480.0,
        "dimensions": "12x14x24 cm",
        "shipping_weight": 650.0,
        "rating": 4.9,
        "review_count": 19,
        "sales": 52,
        "views": 284,
        "featured": False,
        "new_arrival": False,
        "best_seller": True,
        "published": True
    },
    {
        "title": "Astronaut Charging Station Dock",
        "slug": "astronaut-charging-station-dock",
        "short_description": "Whimsical astronaut watch and phone stand with integrated smart charger routing.",
        "description": "Let a tiny astronaut support your daily devices. Crafted with extreme detail, the astronaut model holds your Apple Watch, Galaxy Watch, or smartphone on its back. The base features a secure channel to tuck away charging wires, maintaining a clean look. Made from weighted composite resin-like PLA, it stands sturdy and double-serves as a beautiful art sculpture when your devices are in use.",
        "price": 1999.00,
        "discount_price": None,
        "category": "Desk Accessories",
        "subcategory": "Custom Gifts",
        "tags": ["gift", "astronaut", "charger", "dock"],
        "thumbnail": "/images/products/astronaut_dock.jpg",
        "gallery": [
            "/images/products/astronaut_dock.jpg",
            "/images/products/astronaut_dock_2.jpg"
        ],
        "videos": [],
        "available_colors": ["Lunar White & Gold", "Cosmos Black & Silver"],
        "available_sizes": ["Standard Fit"],
        "material": "Heavyweight PolyPLA",
        "print_quality": "0.12mm Extra Fine",
        "production_time": "2-3 Days",
        "stock": 20,
        "SKU": "MWM-DA-008",
        "weight": 310.0,
        "dimensions": "12x10x15 cm",
        "shipping_weight": 420.0,
        "rating": 4.9,
        "review_count": 27,
        "sales": 94,
        "views": 440,
        "featured": True,
        "new_arrival": True,
        "best_seller": False,
        "published": True
    }
]

async def seed_database():
    await connect_to_mongo()
    db = get_database()
    
    # Clear existing products
    print("Clearing existing products...")
    await db.products.delete_many({})
    
    # Insert new products
    print(f"Inserting {len(products_seed)} seed products...")
    for prod in products_seed:
        prod["created_at"] = datetime.utcnow()
        prod["updated_at"] = datetime.utcnow()
        await db.products.insert_one(prod)
        print(f"Inserted: {prod['title']}")
        
    print("Database seeding completed successfully!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_database())

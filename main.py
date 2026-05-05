from fastapi import FastAPI
from pydantic import BaseModel
import qrcode
from firebase_db import db   # <-- Firebase connection

app = FastAPI()

# -------------------------
# PRICE LIST
# -------------------------
prices = {
    "milk": 50,
    "bread": 30,
    "chocolate": 20
}

# -------------------------
# REQUEST MODELS
# -------------------------
class Item(BaseModel):
    user_id: str
    product: str

class User(BaseModel):
    user_id: str

# -------------------------
# ROOT CHECK
# -------------------------
@app.get("/")
def home():
    return {"message": "Backend is running with Firebase"}

# -------------------------
# ADD ITEM (Firebase)
# -------------------------
@app.post("/add-item")
async def add_item(item: Item):
    ref = db.collection("cart").document(item.user_id)

    cart = ref.get().to_dict() or {}

    cart[item.product] = cart.get(item.product, 0) + 1

    ref.set(cart)

    return {
        "status": "added",
        "cart": cart
    }

# -------------------------
# REMOVE ITEM (Firebase)
# -------------------------
@app.post("/remove-item")
async def remove_item(item: Item):
    ref = db.collection("cart").document(item.user_id)

    cart = ref.get().to_dict() or {}

    if item.product in cart:
        cart[item.product] -= 1

        if cart[item.product] <= 0:
            del cart[item.product]

    ref.set(cart)

    return {
        "status": "removed",
        "cart": cart
    }

# -------------------------
# GET CART (Firebase)
# -------------------------
@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    cart = db.collection("cart").document(user_id).get().to_dict()
    return cart or {}

# -------------------------
# GENERATE BILL + QR
# -------------------------
@app.post("/generate-bill")
async def generate_bill(user: User):
    cart = db.collection("cart").document(user.user_id).get().to_dict() or {}

    total = sum(prices[item] * qty for item, qty in cart.items())

    # Generate QR
    upi_link = f"upi://pay?pa=demo@upi&am={total}&cu=INR"
    img = qrcode.make(upi_link)
    img.save("qr.png")

    return {
        "status": "bill_generated",
        "total": total,
        "cart": cart,
        "qr_file": "qr.png"
    }

# -------------------------
# VALIDATE CART (Firebase)
# -------------------------
@app.post("/validate-cart")
async def validate_cart(data: dict):
    user_id = data["user_id"]
    detected_items = data["detected_items"]

    detected_count = {}
    for item in detected_items:
        detected_count[item] = detected_count.get(item, 0) + 1

    stored_cart = db.collection("cart").document(user_id).get().to_dict() or {}

    if detected_count != stored_cart:
        return {
            "status": "mismatch",
            "detected": detected_count,
            "stored": stored_cart
        }

    return {"status": "ok"} 
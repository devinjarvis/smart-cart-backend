from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import qrcode
import base64
from io import BytesIO

from firebase_db import db  # Firebase connection

app = FastAPI(
    title="Smart Cart API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# -------------------------------
# Product price list
# -------------------------------
prices = {
    "milk": 50,
    "bread": 30,
    "eggs": 70,
    "chocolate": 40
}

# -------------------------------
# Request models
# -------------------------------
class Item(BaseModel):
    user_id: str
    product: str

class User(BaseModel):
    user_id: str

# -------------------------------
# Home route
# -------------------------------
@app.get("/")
def home():
    return {"message": "Backend is running"}

# -------------------------------
# Add item
# -------------------------------
@app.post("/add-item")
def add_item(item: Item):
    doc_ref = db.collection("cart").document(item.user_id)
    cart = doc_ref.get().to_dict() or {}

    cart[item.product] = cart.get(item.product, 0) + 1
    doc_ref.set(cart)

    return {"status": "added", "cart": cart}

# -------------------------------
# Remove item
# -------------------------------
@app.post("/remove-item")
def remove_item(item: Item):
    doc_ref = db.collection("cart").document(item.user_id)
    cart = doc_ref.get().to_dict() or {}

    if item.product in cart:
        cart[item.product] -= 1
        if cart[item.product] <= 0:
            del cart[item.product]

    doc_ref.set(cart)
    return {"status": "removed", "cart": cart}

# -------------------------------
# Get cart
# -------------------------------
@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    doc_ref = db.collection("cart").document(user_id)
    cart = doc_ref.get().to_dict() or {}
    return cart

# -------------------------------
# Generate bill + QR
# -------------------------------
@app.post("/generate-bill")
def generate_bill(user: User):
    doc_ref = db.collection("cart").document(user.user_id)
    cart = doc_ref.get().to_dict() or {}

    total = 0
    for item, qty in cart.items():
        total += prices.get(item, 0) * qty

    # Create QR
    qr_data = f"Pay ₹{total}"
    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "cart": cart,
        "total": total,
        "qr": qr_base64
    }

# -------------------------------
# Simple UI for demo
# -------------------------------
@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <head>
        <title>Smart Cart</title>
        <style>
            body { font-family: Arial; text-align: center; margin-top: 50px; }
            input, button { padding: 10px; margin: 10px; }
        </style>
    </head>
    <body>
        <h1>Smart Shopping Cart</h1>

        <input id="user" value="u1" placeholder="User ID"><br>
        <input id="product" placeholder="Product"><br>

        <button onclick="add()">Add</button>
        <button onclick="remove()">Remove</button>
        <button onclick="bill()">Generate Bill</button>

        <pre id="output"></pre>

        <script>
            async function add() {
                let res = await fetch("/add-item", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: user.value,
                        product: product.value
                    })
                });
                output.innerText = JSON.stringify(await res.json(), null, 2);
            }

            async function remove() {
                let res = await fetch("/remove-item", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: user.value,
                        product: product.value
                    })
                });
                output.innerText = JSON.stringify(await res.json(), null, 2);
            }

            async function bill() {
                let res = await fetch("/generate-bill", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: user.value
                    })
                });
                let data = await res.json();

                output.innerText = JSON.stringify(data, null, 2);

                let img = document.createElement("img");
                img.src = "data:image/png;base64," + data.qr;
                document.body.appendChild(img);
            }
        </script>
    </body>
    </html>
    """
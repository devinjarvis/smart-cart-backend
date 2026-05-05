from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import qrcode
import base64
from io import BytesIO
import json

# 🔥 Firebase
from firebase_db import db

app = FastAPI()

# ----------------------------
# Models
# ----------------------------
class Item(BaseModel):
    user_id: str
    product: str

class User(BaseModel):
    user_id: str

# ----------------------------
# Home Routes (IMPORTANT)
# ----------------------------
@app.get("/")
def home():
    return {"message": "Home working"}

@app.get("/check")
def check():
    return {"status": "ok"}

@app.get("/test")
def test():
    return {"message": "Backend running"}

# ----------------------------
# Add Item
# ----------------------------
@app.post("/add-item")
def add_item(item: Item):
    ref = db.collection("cart").document(item.user_id)
    doc = ref.get()

    cart = doc.to_dict() if doc.exists else {}

    cart[item.product] = cart.get(item.product, 0) + 1
    ref.set(cart)

    return {"message": "Item added", "cart": cart}

# ----------------------------
# Remove Item
# ----------------------------
@app.post("/remove-item")
def remove_item(item: Item):
    ref = db.collection("cart").document(item.user_id)
    doc = ref.get()

    if not doc.exists:
        return {"error": "Cart empty"}

    cart = doc.to_dict()

    if item.product in cart:
        cart[item.product] -= 1
        if cart[item.product] <= 0:
            del cart[item.product]

    ref.set(cart)

    return {"message": "Item removed", "cart": cart}

# ----------------------------
# Get Cart
# ----------------------------
@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    doc = db.collection("cart").document(user_id).get()
    return doc.to_dict() if doc.exists else {}

# ----------------------------
# Generate Bill
# ----------------------------
@app.post("/generate-bill")
def generate_bill(user: User):
    doc = db.collection("cart").document(user.user_id).get()

    if not doc.exists:
        return {"error": "Cart empty"}

    cart = doc.to_dict()

    # Simple pricing logic
    total = sum(v * 50 for v in cart.values())

    bill_data = {
        "user": user.user_id,
        "cart": cart,
        "total": total
    }

    # Generate QR
    qr = qrcode.make(json.dumps(bill_data))
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "cart": cart,
        "total": total,
        "qr": qr_base64
    }

# ----------------------------
# UI (UPDATED CLEAN VERSION)
# ----------------------------
@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <head>
        <title>Smart Cart</title>
        <style>
            body {
                font-family: Arial;
                background: #f5f5f5;
                text-align: center;
                margin-top: 50px;
            }

            .card {
                background: white;
                padding: 30px;
                width: 350px;
                margin: auto;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }

            input {
                width: 90%;
                padding: 10px;
                margin: 8px;
                border-radius: 5px;
                border: 1px solid #ccc;
            }

            button {
                padding: 10px 15px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }

            .add { background: #4CAF50; color: white; }
            .remove { background: #f44336; color: white; }
            .bill { background: #2196F3; color: white; }

            #output {
                margin-top: 20px;
                text-align: left;
                font-size: 14px;
            }

            img {
                margin-top: 20px;
            }
        </style>
    </head>

    <body>

        <div class="card">
            <h2>🛒 Smart Cart</h2>

            <input id="user" placeholder="User ID" value="u1"><br>
            <input id="product" placeholder="Product name"><br>

            <button class="add" onclick="addItem()">Add</button>
            <button class="remove" onclick="removeItem()">Remove</button>
            <button class="bill" onclick="bill()">Generate Bill</button>

            <div id="output"></div>
            <img id="qr" width="200"/>
        </div>

        <script>
            const base = window.location.origin;

            async function addItem() {
                const user = document.getElementById("user").value;
                const product = document.getElementById("product").value;

                await fetch(base + "/add-item", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({user_id: user, product: product})
                });

                document.getElementById("output").innerText = "Item added!";
            }

            async function removeItem() {
                const user = document.getElementById("user").value;
                const product = document.getElementById("product").value;

                await fetch(base + "/remove-item", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({user_id: user, product: product})
                });

                document.getElementById("output").innerText = "Item removed!";
            }

            async function bill() {
                const user = document.getElementById("user").value;

                const res = await fetch(base + "/generate-bill", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({user_id: user})
                });

                const data = await res.json();

                document.getElementById("output").innerText =
                    "Cart:\\n" + JSON.stringify(data.cart, null, 2) +
                    "\\n\\nTotal: ₹" + data.total;

                document.getElementById("qr").src =
                    "data:image/png;base64," + data.qr;
            }
        </script>

    </body>
    </html>
    """
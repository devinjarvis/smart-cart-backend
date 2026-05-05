from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import base64
import qrcode
import io

from firebase_db import db

app = FastAPI()

# =========================
# MODEL
# =========================
class Item(BaseModel):
    user_id: str
    item: str


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"message": "Smart Cart Backend Running"}


# =========================
# UI
# =========================
@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <head>
        <title>Smart Cart</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f6f8;
                padding: 20px;
            }

            h1 {
                text-align: center;
                margin-bottom: 20px;
            }

            .container {
                max-width: 900px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }

            input {
                padding: 10px;
                margin: 5px;
                width: 200px;
            }

            button {
                padding: 8px 12px;
                margin: 5px;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }

            .btn-green { background: #4CAF50; color: white; }
            .btn-red { background: #f44336; color: white; }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            th, td {
                padding: 10px;
                text-align: center;
                border-bottom: 1px solid #ddd;
            }

            .total-box {
                margin-top: 20px;
                padding: 15px;
                background: #e8f5e9;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            }

            .actions {
                margin-top: 20px;
                text-align: center;
            }

            img {
                margin-top: 20px;
            }
        </style>
    </head>

    <body>

    <div class="container">
        <h1>🛒 Smart Cart</h1>

        <input id="user" value="u1" placeholder="User ID">
        <input id="product" placeholder="Detected item">

        <div>
            <button class="btn-green" onclick="add()">Add</button>
            <button class="btn-red" onclick="remove()">Remove</button>
        </div>

        <table id="cartTable">
            <tr>
                <th>Item</th>
                <th>Quantity</th>
            </tr>
        </table>

        <div class="total-box" id="total">
            Total: ₹0
        </div>

        <div class="actions">
            <button class="btn-green" onclick="generateBill()">Generate Bill</button>
            <button class="btn-red" onclick="clearCart()">Clear Cart</button>
        </div>

        <div id="qr"></div>
    </div>

    <script>

        async function loadCart() {
            let user = document.getElementById("user").value;

            let res = await fetch(`/cart/${user}`);
            let data = await res.json();

            let table = document.getElementById("cartTable");
            table.innerHTML = "<tr><th>Item</th><th>Quantity</th></tr>";

            let total = 0;

            for (let item in data) {
                table.innerHTML += `
                    <tr>
                        <td>${item}</td>
                        <td>${data[item]}</td>
                    </tr>
                `;
                total += data[item] * 100;
            }

            document.getElementById("total").innerText = "Total: ₹" + total;
        }

        async function add() {
            let user = document.getElementById("user").value;
            let product = document.getElementById("product").value;

            await fetch("/add-item", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: user, item: product})
            });

            loadCart();
        }

        async function remove() {
            let user = document.getElementById("user").value;
            let product = document.getElementById("product").value;

            await fetch("/remove-item", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: user, item: product})
            });

            loadCart();
        }

        async function generateBill() {
            let user = document.getElementById("user").value;

            let res = await fetch("/generate-bill", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: user, item: ""})
            });

            let data = await res.json();

            document.getElementById("qr").innerHTML =
                `<img src="data:image/png;base64,${data.qr}" width="200"/>`;
        }

        async function clearCart() {
            let user = document.getElementById("user").value;

            await fetch(`/clear-cart/${user}`, {
                method: "POST"
            });

            loadCart();
        }

        loadCart();

    </script>

    </body>
    </html>
    """


# =========================
# ADD ITEM
# =========================
@app.post("/add-item")
def add_item(data: Item):
    ref = db.collection("cart").document(data.user_id)
    doc = ref.get()

    cart = doc.to_dict() if doc.exists else {}

    cart[data.item] = cart.get(data.item, 0) + 1
    ref.set(cart)

    return {"cart": cart}


# =========================
# REMOVE ITEM
# =========================
@app.post("/remove-item")
def remove_item(data: Item):
    ref = db.collection("cart").document(data.user_id)
    doc = ref.get()

    if not doc.exists:
        return {"cart": {}}

    cart = doc.to_dict()

    if data.item in cart:
        cart[data.item] -= 1
        if cart[data.item] <= 0:
            del cart[data.item]

    ref.set(cart)
    return {"cart": cart}


# =========================
# CLEAR CART
# =========================
@app.post("/clear-cart/{user_id}")
def clear_cart(user_id: str):
    db.collection("cart").document(user_id).delete()
    return {"status": "cleared"}


# =========================
# GET CART
# =========================
@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    doc = db.collection("cart").document(user_id).get()
    return doc.to_dict() if doc.exists else {}


# =========================
# GENERATE BILL + QR
# =========================
@app.post("/generate-bill")
def generate_bill(data: Item):
    doc = db.collection("cart").document(data.user_id).get()
    cart = doc.to_dict() if doc.exists else {}

    total = sum(cart.values()) * 100

    qr_data = f"User: {data.user_id}, Total: ₹{total}"

    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "cart": cart,
        "total": total,
        "qr": qr_base64
    }
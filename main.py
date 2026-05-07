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
<!DOCTYPE html>
<html>
<head>
    <title>Smart Cart</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>

        *{
            margin:0;
            padding:0;
            box-sizing:border-box;
            font-family: Arial, sans-serif;
        }

        body{
            background:#f4f6fb;
            padding:30px;
        }

        .header{
            width:100%;
            background:linear-gradient(90deg,#1d2671,#c33764);
            color:white;
            padding:20px 40px;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:30px;
            box-shadow:0 5px 15px rgba(0,0,0,0.1);
        }

        .header h1{
            font-size:40px;
        }

        .header p{
            margin-top:5px;
            opacity:0.9;
        }

        .container{
            display:grid;
            grid-template-columns:2fr 1fr;
            gap:25px;
        }

        .card{
            background:white;
            border-radius:20px;
            padding:25px;
            box-shadow:0 4px 15px rgba(0,0,0,0.08);
        }

        .section-title{
            font-size:26px;
            font-weight:bold;
            margin-bottom:20px;
            color:#333;
        }

        .input-group{
            display:flex;
            gap:15px;
            margin-bottom:20px;
        }

        input{
            flex:1;
            padding:14px;
            border-radius:12px;
            border:1px solid #ddd;
            font-size:16px;
        }

        button{
            border:none;
            padding:14px 22px;
            border-radius:12px;
            font-size:16px;
            cursor:pointer;
            font-weight:bold;
            transition:0.3s;
        }

        .add-btn{
            background:#28c76f;
            color:white;
        }

        .remove-btn{
            background:#ea5455;
            color:white;
        }

        .bill-btn{
            background:#28c76f;
            color:white;
            width:100%;
            margin-top:20px;
        }

        .clear-btn{
            background:#ea5455;
            color:white;
            width:100%;
            margin-top:15px;
        }

        button:hover{
            transform:scale(1.03);
        }

        table{
            width:100%;
            border-collapse:collapse;
            margin-top:20px;
        }

        th{
            background:#f3f3f3;
            padding:15px;
            text-align:left;
        }

        td{
            padding:15px;
            border-bottom:1px solid #eee;
        }

        .total-box{
            margin-top:20px;
            background:#eaf8ef;
            padding:20px;
            border-radius:15px;
            font-size:28px;
            font-weight:bold;
            color:#28a745;
            text-align:center;
        }

        .payment-card{
            text-align:center;
        }

        .payment-card h2{
            margin-bottom:15px;
            color:#6f42c1;
        }

        .qr-box{
            background:#fafafa;
            padding:20px;
            border-radius:20px;
            margin-top:20px;
            border:2px dashed #ccc;
        }

        .qr-box img{
            width:260px;
            margin-top:10px;
        }

        .payment-note{
            margin-top:15px;
            color:#555;
            line-height:1.6;
        }

        .apps{
            display:flex;
            justify-content:center;
            gap:15px;
            margin-top:20px;
            font-size:20px;
            font-weight:bold;
            color:#555;
        }

        .feature-grid{
            margin-top:30px;
            display:grid;
            grid-template-columns:repeat(4,1fr);
            gap:20px;
        }

        .feature{
            background:white;
            border-radius:18px;
            padding:20px;
            text-align:center;
            box-shadow:0 4px 15px rgba(0,0,0,0.05);
        }

        .feature h3{
            margin-top:10px;
            color:#333;
        }

        .footer{
            text-align:center;
            margin-top:30px;
            color:#777;
        }

        @media(max-width:1000px){

            .container{
                grid-template-columns:1fr;
            }

            .feature-grid{
                grid-template-columns:1fr 1fr;
            }
        }

    </style>
</head>

<body>

    <div class="header">
        <div>
            <h1>🛒 Smart Cart</h1>
            <p>AI Powered Smart Shopping</p>
        </div>

        <div>
            <h3>Smarter Shopping Experience</h3>
        </div>
    </div>

    <div class="container">

        <div>

            <div class="card">

                <div class="section-title">
                    Add / Remove Item
                </div>

                <div class="input-group">

                    <input type="text" id="user" placeholder="User ID" value="u1">

                    <input type="text" id="item" placeholder="Detected item">

                    <button class="add-btn" onclick="addItem()">
                        + Add
                    </button>

                    <button class="remove-btn" onclick="removeItem()">
                        - Remove
                    </button>

                </div>

            </div>

            <div class="card" style="margin-top:25px;">

                <div class="section-title">
                    Cart Items
                </div>

                <table>

                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Quantity</th>
                        </tr>
                    </thead>

                    <tbody id="cart-body">

                    </tbody>

                </table>

                <div class="total-box" id="total">
                    Total: ₹0
                </div>

                <button class="bill-btn" onclick="generateBill()">
                    Generate Bill
                </button>

                <button class="clear-btn" onclick="clearCart()">
                    Clear Cart
                </button>

            </div>

        </div>

        <div>

            <div class="card payment-card">

                <h2>📄 Bill Summary</h2>

                <h1 id="bill-total" style="color:#6f42c1;">
                    ₹0
                </h1>

                <div class="qr-box">

                    <h2>📱 Scan & Pay</h2>

                    <div id="qr"></div>

                    <div class="payment-note">
                        Scan this QR using GPay, PhonePe, Paytm or any UPI app.
                    </div>

                </div>

                <div class="apps">
                    <span>GPay</span>
                    <span>PhonePe</span>
                    <span>Paytm</span>
                </div>

            </div>

        </div>

    </div>

<script>

const prices = {
    "bottle": 50,
    "cup": 80,
    "book": 350,
    "phone": 15000,
    "laptop": 55000
};

const icons = {
    "bottle": "🍼",
    "cup": "☕",
    "book": "📚",
    "phone": "📱",
    "laptop": "💻"
};

async function loadCart(){

    let user = document.getElementById("user").value;

    let res = await fetch(`/cart/${user}`);

    let data = await res.json();

    let body = document.getElementById("cart-body");

    body.innerHTML = "";

    let total = 0;

    for(let item in data){

        let price = prices[item] || 100;

        total += data[item] * price;

        body.innerHTML += `
        <tr>
            <td>${icons[item] || "🛒"} ${item}</td>
            <td>${data[item]}</td>
        </tr>
        `;
    }

    document.getElementById("total").innerHTML =
        `Total: ₹${total}`;

    document.getElementById("bill-total").innerHTML =
        `₹${total}`;
}

async function addItem(){

    let user = document.getElementById("user").value;

    let item = document.getElementById("item").value.toLowerCase();

    await fetch("/add-item",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            user_id:user,
            item:item
        })
    });

    loadCart();
}

async function removeItem(){

    let user = document.getElementById("user").value;

    let item = document.getElementById("item").value.toLowerCase();

    await fetch("/remove-item",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            user_id:user,
            item:item
        })
    });

    loadCart();
}

async function generateBill(){

    let user = document.getElementById("user").value;

    let res = await fetch("/generate-bill",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            user_id:user,
            item:""
        })
    });

    let data = await res.json();

    document.getElementById("bill-total").innerHTML =
        `₹${data.total}`;

    document.getElementById("qr").innerHTML =
        `<img src="data:image/png;base64,${data.qr}" />`;
}

async function clearCart(){

    let user = document.getElementById("user").value;

    await fetch(`/clear-cart/${user}`,{
        method:"POST"
    });

    document.getElementById("qr").innerHTML = "";

    loadCart();
}

loadCart();

setInterval(loadCart, 2000);

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

    prices = {
        "bottle": 50,
        "cup": 80,
        "book": 350,
        "phone": 15000,
        "laptop": 55000
    }

    total = 0

    for item, qty in cart.items():
        total += prices.get(item, 100) * qty

    upi_id = "devinsiju@oksbi"

    upi_link = f"upi://pay?pa={upi_id}&pn=SmartCart&am={total}&cu=INR"

    img = qrcode.make(upi_link)

    buf = io.BytesIO()

    img.save(buf, format="PNG")

    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "cart": cart,
        "total": total,
        "qr": qr_base64
    }
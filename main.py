from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import qrcode, base64
from io import BytesIO

from firebase_db import get_db

print("🔥 FINAL VERSION LOADED 🔥")

app = FastAPI(
    title="Smart Cart API",
    docs_url="/docs",
    redoc_url="/redoc"
)

prices = {
    "milk": 50,
    "bread": 30,
    "eggs": 70,
    "chocolate": 40
}

class Item(BaseModel):
    user_id: str
    product: str

class User(BaseModel):
    user_id: str

@app.get("/")
def home():
    return {"message": "Backend is running"}

@app.get("/check")
def check():
    return {"status": "ok", "version": "FINAL"}

# ---------- Cart APIs ----------

@app.post("/add-item")
def add_item(item: Item):
    db = get_db()
    doc = db.collection("cart").document(item.user_id)
    cart = doc.get().to_dict() or {}
    cart[item.product] = cart.get(item.product, 0) + 1
    doc.set(cart)
    return {"status": "added", "cart": cart}

@app.post("/remove-item")
def remove_item(item: Item):
    db = get_db()
    doc = db.collection("cart").document(item.user_id)
    cart = doc.get().to_dict() or {}

    if item.product in cart:
        cart[item.product] -= 1
        if cart[item.product] <= 0:
            del cart[item.product]

    doc.set(cart)
    return {"status": "removed", "cart": cart}

@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    db = get_db()
    doc = db.collection("cart").document(user_id)
    return doc.get().to_dict() or {}

@app.post("/generate-bill")
def generate_bill(user: User):
    db = get_db()
    doc = db.collection("cart").document(user.user_id)
    cart = doc.get().to_dict() or {}

    total = sum(prices.get(p, 0) * q for p, q in cart.items())

    qr = qrcode.make(f"Pay ₹{total}")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return {"cart": cart, "total": total, "qr": qr_b64}

# ---------- Simple UI ----------

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
    <body style="font-family: Arial; text-align:center; margin-top:40px;">
        <h2>Smart Cart</h2>
        <input id="user" value="u1"><br>
        <input id="product" placeholder="product"><br>
        <button onclick="add()">Add</button>
        <button onclick="remove()">Remove</button>
        <button onclick="bill()">Bill</button>
        <pre id="out"></pre>
        <script>
            async function add(){
              let r=await fetch('/add-item',{method:'POST',headers:{'Content-Type':'application/json'},
              body:JSON.stringify({user_id:user.value,product:product.value})});
              out.innerText=JSON.stringify(await r.json(),null,2);
            }
            async function remove(){
              let r=await fetch('/remove-item',{method:'POST',headers:{'Content-Type':'application/json'},
              body:JSON.stringify({user_id:user.value,product:product.value})});
              out.innerText=JSON.stringify(await r.json(),null,2);
            }
            async function bill(){
              let r=await fetch('/generate-bill',{method:'POST',headers:{'Content-Type':'application/json'},
              body:JSON.stringify({user_id:user.value})});
              let d=await r.json();
              out.innerText=JSON.stringify(d,null,2);
              let img=document.createElement('img');
              img.src="data:image/png;base64,"+d.qr;
              document.body.appendChild(img);
            }
        </script>
    </body>
    </html>
    """
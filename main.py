from fastapi import FastAPI

print("🔥 CLEAN VERSION LOADED 🔥")

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Home working"}

@app.get("/check")
def check():
    return {"status": "ok"}

@app.get("/test")
def test():
    return {"test": "working"}
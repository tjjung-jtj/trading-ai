from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def home():
    return {"status": "AI server running"}

@app.get("/recommend")
def recommend():
    return {
        "crypto": [
            {"symbol": "BTC", "score": random.randint(60, 90)},
            {"symbol": "ETH", "score": random.randint(60, 90)}
        ],
        "stock": [
            {"symbol": "AAPL", "score": random.randint(60, 90)},
            {"symbol": "TSLA", "score": random.randint(60, 90)}
        ]
    }

@app.post("/simulate")
def simulate():
    return {
        "initial": 2000000,
        "final": 2100000,
        "profit_rate": 5.0
    }

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
from datetime import datetime
import json

# -------------------- APP --------------------
app = FastAPI(
    title="NEPSE Pump & Dump Detection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- MODEL --------------------
class StockAnalysis(BaseModel):
    symbol: str
    current_price: float
    price_change_percent: float
    volume: int
    volume_spike: float
    is_suspicious: bool
    risk_level: str
    pattern: str
    reason: str
    timestamp: str

stocks_db: List[StockAnalysis] = []

# -------------------- LOGIC --------------------
def detect_pattern(price_change: float, volume_spike: float) -> str:
    if volume_spike >= 3 and price_change >= 5:
        return "Potential PUMP"
    elif volume_spike >= 3 and price_change <= -5:
        return "Potential DUMP"
    elif volume_spike >= 2 or abs(price_change) >= 3:
        return "Unusual Activity"
    return "Normal Trading"

def determine_risk(price_change: float, volume_spike: float) -> str:
    """
    Realistic thresholds for distributing risks:
    - HIGH: significant price move + large spike
    - MEDIUM: moderate move/spike
    - LOW: small changes
    """
    if volume_spike >= 3 and abs(price_change) >= 5:
        return "HIGH"
    elif volume_spike >= 1.8 or abs(price_change) >= 3:
        return "MEDIUM"
    else:
        return "LOW"

def generate_reason(risk: str, price_change: float, volume_spike: float) -> str:
    if risk == "HIGH":
        return f"⚠️ {volume_spike:.1f}x volume, {price_change:.1f}% move"
    elif risk == "MEDIUM":
        return f"Moderate spike: {volume_spike:.1f}x volume, {price_change:.1f}% change"
    return "Normal trading behavior"

def load_nepse_data():
    from pathlib import Path
    import json
    from datetime import datetime

    BASE_DIR = Path(__file__).resolve().parent.parent
    json_path = BASE_DIR / "data" / "nepse_today.json"
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    analyzed = []
    
    for s in raw["result"]["stocks"]:
        current_price = s.get("closingPrice", 0.0)
        price_change = s.get("percentChange", 0.0)
        volume = s.get("volume", 0)
        
        # Baseline average volume: assume 20% of current volume
        avg_volume = max(volume * 0.2, 1)
        volume_spike = round(volume / avg_volume, 2)
        
        risk = determine_risk(price_change, volume_spike)
        pattern = detect_pattern(price_change, volume_spike)
        reason = generate_reason(risk, price_change, volume_spike)
        
        analyzed.append(
            StockAnalysis(
                symbol=s.get("stockSymbol", "N/A"),
                current_price=current_price,
                price_change_percent=price_change,
                volume=volume,
                volume_spike=volume_spike,
                is_suspicious=risk in ["HIGH", "MEDIUM"],
                risk_level=risk,
                pattern=pattern,
                reason=reason,
                timestamp=datetime.now().isoformat()
            )
        )
    
    return analyzed

# -------------------- INIT --------------------
stocks_db = load_nepse_data()
print(f"✅ Loaded {len(stocks_db)} stocks")

# -------------------- API --------------------
@app.get("/")
def root():
    return {"message": "NEPSE API", "total_stocks": len(stocks_db)}

@app.get("/stocks", response_model=List[StockAnalysis])
def get_stocks():
    return stocks_db

@app.get("/stocks/suspicious", response_model=List[StockAnalysis])
def get_suspicious():
    return [s for s in stocks_db if s.is_suspicious]

@app.get("/stocks/{symbol}", response_model=StockAnalysis)
def get_stock(symbol: str):
    for s in stocks_db:
        if s.symbol.upper() == symbol.upper():
            return s
    raise HTTPException(status_code=404, detail="Stock not found")

@app.get("/stats")
def stats():
    return {
        "total_stocks": len(stocks_db),
        "high_risk": len([s for s in stocks_db if s.risk_level == "HIGH"]),
        "medium_risk": len([s for s in stocks_db if s.risk_level == "MEDIUM"]),
        "low_risk": len([s for s in stocks_db if s.risk_level == "LOW"]),
    }


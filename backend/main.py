from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
from datetime import datetime, timedelta
import statistics

app = FastAPI(title="NEPSE Pump & Dump Detector")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class StockAnalysis(BaseModel):
    symbol: str
    current_price: float
    price_change_percent: float
    volume: float
    risk_score: int
    risk_level: str
    signals: List[str]

class Alert(BaseModel):
    id: int
    stock_symbol: str
    alert_type: str
    message: str
    timestamp: str
    risk_level: str

# In-memory storage
alerts_db = []
alert_counter = 0

@app.get("/")
def read_root():
    return {"message": "NEPSE Pump & Dump Detection API", "status": "running"}

@app.get("/api/market-overview")
def get_market_overview():
    """Get overall NEPSE market data"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        url = f"https://www.nepalipaisa.com/api/GetIndexSubIndexHistory?indexName=Nepse&fromDate=2022-07-01&toDate=2025-12-15&_=1765812084416"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                latest = data[-1]
                previous = data[-2] if len(data) > 1 else latest
                
                change = latest.get('close', 0) - previous.get('close', 0)
                change_percent = (change / previous.get('close', 1)) * 100 if previous.get('close', 0) != 0 else 0
                
                return {
                    "index_value": latest.get('close', 0),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "date": latest.get('date', end_date),
                    "volume": latest.get('totalTurnover', 0)
                }
        
        return {"error": "Unable to fetch market data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/today")
def get_today_stocks():
    """Get today's stock prices"""
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.nepalipaisa.com/api/GetTodaySharePrice?stockSymbol=&tradeDate={date}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {"stocks": data[:50], "total": len(data)}
        
        return {"stocks": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/{symbol}")
def analyze_stock(symbol: str):
    """Analyze a specific stock for pump-and-dump patterns"""
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.nepalipaisa.com/api/GetTodaySharePrice?stockSymbol={symbol}&tradeDate={date}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data or len(data) == 0:
                raise HTTPException(status_code=404, detail="Stock not found")
            
            stock = data[0]
            
            # Simple pump-and-dump detection logic
            price_change = stock.get('percentageChange', 0)
            volume = stock.get('totalTradeQuantity', 0)
            ltp = stock.get('lastTradedPrice', 0)
            
            signals = []
            risk_score = 0
            
            # Check for unusual price increase
            if price_change > 10:
                signals.append("Unusual price spike detected (+10%)")
                risk_score += 40
            elif price_change > 5:
                signals.append("Significant price increase (+5%)")
                risk_score += 20
            
            # Check for high volume
            if volume > 100000:
                signals.append("High trading volume detected")
                risk_score += 30
            elif volume > 50000:
                signals.append("Elevated trading volume")
                risk_score += 15
            
            # Check for price volatility
            high = stock.get('highPrice', 0)
            low = stock.get('lowPrice', 0)
            if high > 0 and low > 0:
                volatility = ((high - low) / low) * 100
                if volatility > 5:
                    signals.append(f"High volatility ({volatility:.1f}%)")
                    risk_score += 20
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = "High"
            elif risk_score >= 40:
                risk_level = "Medium"
            else:
                risk_level = "Low"
                if not signals:
                    signals.append("No suspicious patterns detected")
            
            return StockAnalysis(
                symbol=symbol,
                current_price=ltp,
                price_change_percent=price_change,
                volume=volume,
                risk_score=min(risk_score, 100),
                risk_level=risk_level,
                signals=signals
            )
        
        raise HTTPException(status_code=404, detail="Stock data not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suspicious-stocks")
def get_suspicious_stocks():
    """Get list of potentially suspicious stocks"""
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.nepalipaisa.com/api/GetTodaySharePrice?stockSymbol=&tradeDate={date}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            suspicious = []
            
            for stock in data:
                price_change = stock.get('percentageChange', 0)
                volume = stock.get('totalTradeQuantity', 0)
                
                # Filter suspicious stocks
                if price_change > 5 or volume > 50000:
                    suspicious.append({
                        "symbol": stock.get('symbol', 'N/A'),
                        "ltp": stock.get('lastTradedPrice', 0),
                        "change_percent": price_change,
                        "volume": volume,
                        "risk_indicator": "High" if price_change > 10 else "Medium"
                    })
            
            # Sort by price change
            suspicious.sort(key=lambda x: x['change_percent'], reverse=True)
            
            return {"suspicious_stocks": suspicious[:20], "total": len(suspicious)}
        
        return {"suspicious_stocks": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts", response_model=List[Alert])
def get_alerts():
    """Get all alerts"""
    return alerts_db

@app.post("/api/alerts")
def create_alert(alert: dict):
    """Create a new alert"""
    global alert_counter
    alert_counter += 1
    
    new_alert = Alert(
        id=alert_counter,
        stock_symbol=alert.get('stock_symbol', 'N/A'),
        alert_type=alert.get('alert_type', 'price_spike'),
        message=alert.get('message', 'Alert created'),
        timestamp=datetime.now().isoformat(),
        risk_level=alert.get('risk_level', 'Medium')
    )
    
    alerts_db.append(new_alert)
    
    # Keep only last 50 alerts
    if len(alerts_db) > 50:
        alerts_db.pop(0)
    
    return new_alert

@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int):
    """Delete an alert"""
    global alerts_db
    alerts_db = [a for a in alerts_db if a.id != alert_id]
    return {"message": "Alert deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
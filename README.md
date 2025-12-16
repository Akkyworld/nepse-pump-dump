
# NEPSE Pump-and-Dump Detection System

A beginner-friendly Python project for detecting potential pump-and-dump schemes in Nepal Stock Exchange (NEPSE) using simple statistical analysis.

## Project Structure

```
nepse-pump-dump/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   ├── app.py              # Streamlit application
│   └── requirements.txt    # Frontend dependencies
├── data/
│   └── nepse_today.json   # Sample stock data
└── README.md
```

## What This Project Does

1. **Analyzes Stock Data**: Examines volume and price patterns
2. **Detects Suspicious Activity**: Flags stocks with:
   - Unusual volume spikes (3x normal volume)
   - Significant price increases (>5%)
   - Rapid price drops after spikes
3. **Risk Scoring**: Assigns risk levels (Low, Medium, High)
4. **Visualization**: Shows trends and patterns in a simple UI

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:
```bash
python main.py
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

The frontend will be available at `http://localhost:8501`

## Usage Guide

1. **Start Backend**: Run `python main.py`  or `uvicorn main:app --reload --port 8000` in the backend folder
2. **Start Frontend**: Run `streamlit run app.py` in the frontend folder
3. **Navigate the UI**:
   - View all analyzed stocks
   - Add new stock data for analysis
   - View suspicious stocks only
   - See detailed analysis for each stock

## API Endpoints

### Get All Stocks
```bash
GET http://localhost:8000/stocks
```

### Get Suspicious Stocks Only
```bash
GET http://localhost:8000/stocks/suspicious
```

### Analyze New Stock
```bash
POST http://localhost:8000/stocks/analyze
Content-Type: application/json

{
        "stockSymbol": "CBBL",
        "companyName": "Citizens Bank International Ltd.",
        "noOfTransactions": 120,
        "maxPrice": 1200.0,
        "minPrice": 1100.0,
        "openingPrice": 1105.0,
        "closingPrice": 1180.0,
        "amount": 3500000.0,
        "previousClosing": 1100.0,
        "differenceRs": 80.0,
        "percentChange": 7.27,
        "volume": 45000,
        "ltv": 0,
        "asOfDate": "2025-12-15T15:00:00",
        "asOfDateString": "As of Mon, 15 Dec 2025 | 03:00:00 PM",
        "tradeDate": "2025-12-15",
        "dataType": null
      }
```

### Get Stock Analysis by Symbol
```bash
GET http://localhost:8000/stocks/NABIL
```

## How Pump-and-Dump Detection Works

Our system uses simple rules to identify suspicious patterns:

1. **Volume Spike Detection**
   - Compares current volume to average volume
   - Flags if volume is 3x or more than normal

2. **Price Movement Analysis**
   - Checks for rapid price increases (>5%)
   - Monitors for subsequent price drops

3. **Risk Scoring**
   - **High Risk**: Volume spike + large price increase + price drop
   - **Medium Risk**: Volume spike + price increase
   - **Low Risk**: Normal trading patterns

4. **Pattern Recognition**
   - Identifies "pump" patterns (volume + price up)
   - Detects "dump" patterns (volume + price down after spike)

## Technologies Used

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit, Requests, Pandas, Plotly
- **Data Analysis**: NumPy (for simple calculations)
- **Python**: 3.8+

## Learning Objectives

This project demonstrates:
- REST API design and implementation
- HTTP methods (GET, POST)
- Data validation with Pydantic
- Frontend-backend communication
- Basic data analysis and pattern detection
- Statistical calculations (averages, percentages)
- Data visualization

## Sample Data Format

json format for stock data:
```json
{
        "stockSymbol": "CBBL",
        "companyName": "Citizens Bank International Ltd.",
        "noOfTransactions": 120,
        "maxPrice": 1200.0,
        "minPrice": 1100.0,
        "openingPrice": 1105.0,
        "closingPrice": 1180.0,
        "amount": 3500000.0,
        "previousClosing": 1100.0,
        "differenceRs": 80.0,
        "percentChange": 7.27,
        "volume": 45000,
        "ltv": 0,
        "asOfDate": "2025-12-15T15:00:00",
        "asOfDateString": "As of Mon, 15 Dec 2025 | 03:00:00 PM",
        "tradeDate": "2025-12-15",
        "dataType": null
      }
```

## Future Enhancements:

- Add real NEPSE data integration
- Implement actual machine learning (scikit-learn)
- Add more sophisticated detection algorithms
- Include historical data analysis
- Add email alerts for suspicious activity

## Project Members
```
Abhinav Bhetuwal
Manish Kumar Yadav
Shuvam Devkota ```

## Course

Prg200: Introduction to Python - Westcliff University

## License


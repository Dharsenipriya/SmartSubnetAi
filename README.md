# 🌐 SmartSubnet AI

**Predictive IP Allocation for Scalable Data Centers**

## Features

✅ **AI-Powered Predictions**: Forecast subnet utilization 7-30 days ahead  
✅ **Auto-Healing**: Detect and resolve IP conflicts automatically  
✅ **Real-Time Monitoring**: Track network health 24/7  
✅ **Smart Allocation**: VLSM-based efficient IP distribution  
✅ **Interactive Dashboard**: Beautiful web interface for management  
✅ Automatic alert checking after each task
✅ Conflict alerts when conflicts are found
✅ Utilization alerts every 30 minutes
✅ Prediction alerts when ML forecasts critical capacity
✅ Daily reports at 9:00 AM
✅ All alerts logged to console and file
✅ No manual intervention needed



## Quick Start

### 1. Install Dependencies

pip install -r requirements.txt

### 2. Generate Sample Data

python data_collector.py

### 3. Run Demo

python main.py --demo

### 4. Launch Dashboard

streamlit run dashboard.py

## Project Structure

SmartSubnetAI/
├── main.py                  ✅ UPDATED (alerts integrated)
├── alert_manager.py         ✅ NEW (console logger)
├── database.py              ✅ Already exists
├── data_collector.py        ✅ Already exists
├── ml_predictor.py          ✅ Already exists
├── conflict_resolver.py     ✅ Already exists
├── dashboard.py             ✅ Already exists
├── smartsubnet.db           ✅ Database
└── smartsubnet_alerts.log   ✅ NEW (alert log file)



## Usage

### Run in Continuous Mode

python main.py --continuous


This runs:
- Data collection every 5 minutes
- Conflict scans every 15 minutes
- ML predictions every 6 hours
- Daily reports at 9 AM

### Run Tests

python test_system.py


## Technologies

- **Backend**: Python 3.9+
- **ML**: scikit-learn, Prophet
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Streamlit
- **Visualization**: Plotly, Matplotlib

## Complete File List

✅ subnet_calculator.py - Subnetting engine

✅ ip_validator.py - IP validation

✅ database.py - Database system

✅ data_collector.py - Data collection

✅ ml_predictor.py - ML predictions

✅ conflict_resolver.py - Conflict resolution

✅ dashboard.py - Web dashboard

✅ main.py - Main orchestrator

✅ test_system.py - Test suite

✅ requirements.txt - Dependencies

✅ README.md - Documentation

✅ smartsubnet.db - Database file (auto-generated)

## HOW TO USE 

Option 1: Full Demo

# 1. Generate 30 days of historical data

python data_collector.py

# 2. Run complete demo

python main.py --demo

# 3. View in dashboard

streamlit run dashboard.py

## Option 2: Production Mode

# Run continuous monitoring (leave running)

python main.py --continuous

In another terminal:

# Check your alert log:

type smartsubnet_alerts.log

# View live dashboard

streamlit run dashboard.py

## What Each Component Does

* Subnet Calculator: Creates optimal IP allocations using VLSM

* Data Collector: Simulates network device monitoring (would connect to real devices in production)

* ML Predictor: Forecasts utilization trends to prevent capacity issues

* Conflict Resolver: Automatically detects and fixes duplicate IPs

* Dashboard: Beautiful web interface to view everything

## Summary 

✅ Network subnetting and IP addressing

✅ Database design and ORM (SQLAlchemy)

✅ Machine learning (time series forecasting)

✅ Web development (Streamlit)

✅ System integration and orchestration

✅ Automated testing

✅ Software architecture

## License

MIT License - Free to use and modify

## Author

Dharseni priya.SJ - SmartSubnet AI v1.0

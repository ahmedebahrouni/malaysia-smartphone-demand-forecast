# 📱 Malaysia Smartphone Demand Forecast (2026–2028)

**How many smartphones will Malaysians buy in the next three years, and which brands will win?**

A personal end-to-end data project: data modelling → feature engineering → machine-learning forecast → Power BI dashboard.
It forecasts quarterly unit sales for the Malaysian smartphone market by brand (Samsung, Apple, Xiaomi, Oppo, Vivo and others) for 2026–2028.

> ⚠️ **About the data:** the dataset is **simulated** (`data/generate_data.py`, seeded), not real sales figures, and this is not client work.
> It is designed to behave like a real consumer-electronics market: population and income growth, festive seasonality (CNY, Hari Raya, 11.11/12.12), the 2020 COVID dip, the 5G rollout from 2022, promotions and flagship launch cycles.
> Drop in a real export (DOSM, IDC or Statista) with the same columns and the whole pipeline runs unchanged.

---

## 🔑 Key results

| Year | Total units (M) | Samsung (M) | Samsung share |
|------|----------------:|------------:|--------------:|
| 2024 (actual) | 12.10 | 3.41 | 28.2% |
| 2025 (actual) | 12.36 | 3.42 | 27.7% |
| 2026 (forecast) | **12.82** | **3.50** | 27.3% |
| 2027 (forecast) | **13.34** | **3.55** | 26.6% |
| 2028 (forecast) | **13.79** | **3.59** | 26.1% |

**Insights**
- The market is forecast to grow about **3.7% a year**, from 12.4M units in 2025 to 13.8M in 2028.
- **Samsung stays #1** but slowly loses share (27.7% → 26.1%) as **Apple** (18.0% → 19.8%) and **Xiaomi** (22.9% → 23.6%) gain.
- **Q4 is the peak quarter** every year (11.11, 12.12 and year-end promotions), about 10% above the average quarter (Q2 is the low point, about 10% below), so stock and marketing budget should be front-loaded into Q3.

**Model accuracy (backtest, trained to 2023 and tested on 2024–2025)**

| Model | MAPE |
|-------|-----:|
| Seasonal naive (same quarter last year) | 5.3% |
| Gradient Boosting (scikit-learn) | **5.1%** |

The final forecast blends Gradient Boosting (seasonality, promotions, macro drivers) with a seasonal-trend estimate, because tree models can't extrapolate a growth trend on their own.

---

## 🧱 Project structure

```
├── data/
│   ├── generate_data.py              # seeded simulation of the market (240 rows: 40 quarters × 6 brands)
│   └── malaysia_smartphone_sales.csv
├── src/
│   └── forecast.py                   # features, backtest, 12-quarter forecast, exports
├── outputs/                          # created when you run the pipeline
│   ├── forecast_2026_2028.csv        # quarterly forecast by brand
│   ├── yearly_by_brand.csv           # actual + forecast per year, ready for Power BI
│   ├── total_market_forecast.png
│   └── samsung_forecast.png
├── powerbi/
│   └── DASHBOARD.md                  # data model, DAX measures and page layout
└── requirements.txt
```

## ▶️ Run it

```bash
pip install -r requirements.txt
python data/generate_data.py
python src/forecast.py
```

## 🛠️ Methods
- **Features:** time trend, quarter dummies, lag-1 and lag-4 (same quarter last year), income index, population, promotion intensity, 5G-era flag, brand
- **Validation:** time-based holdout (no random split, so there's no look-ahead leakage), compared against a seasonal-naive baseline
- **Forecast:** recursive 12-quarter forecast per brand, with explicit macro assumptions (income +3.5% a year, population +1.1% a year)
- **BI layer:** a star schema in Power BI with DAX measures for YoY growth, market share and forecast vs actual (see `powerbi/DASHBOARD.md`)

## 🧰 Stack
Python · pandas · NumPy · scikit-learn · Matplotlib · Power BI · DAX

---

👤 **Ahmed Bahrouni**, Data Analyst & Implementation Consultant · [LinkedIn](https://www.linkedin.com/in/ahmed-bahrouni-696a24214)

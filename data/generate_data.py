"""
Generate a SIMULATED quarterly dataset of smartphone unit sales in Malaysia.

The numbers are not real sales figures. They are produced by a seeded model
whose drivers (population growth, household income, 5G rollout, festive
seasonality, price promotions) mimic the shape of a real consumer-electronics
market, so the forecasting pipeline can be built and tested end to end.
Swap in real data (e.g. DOSM, IDC or Statista exports) with the same columns
and the rest of the project runs unchanged.
"""
import numpy as np
import pandas as pd

SEED = 42
BRANDS = {
    # brand: (base share, yearly share drift, avg price MYR)
    "Samsung": (0.27, 0.000, 1900),
    "Xiaomi":  (0.18, 0.006, 900),
    "Apple":   (0.14, 0.004, 4200),
    "Oppo":    (0.16, -0.003, 1100),
    "Vivo":    (0.15, -0.002, 1000),
    "Others":  (0.10, -0.005, 700),
}


def main(path="data/malaysia_smartphone_sales.csv"):
    rng = np.random.default_rng(SEED)
    quarters = pd.period_range("2016Q1", "2025Q4", freq="Q")
    rows = []
    for i, q in enumerate(quarters):
        t = i / 4  # years since 2016
        population_m = 31.2 * (1.011 ** t)
        income_idx = 100 * (1.035 ** t) * (0.93 if q.year == 2020 else 1.0)
        fiveg = 1.0 if q >= pd.Period("2022Q1", "Q") else 0.0
        # Q1: Chinese New Year / Hari Raya promos, Q4: 11.11 / 12.12 / year-end
        season = {1: 1.06, 2: 0.95, 3: 0.97, 4: 1.12}[q.quarter]
        covid = 0.82 if q in pd.period_range("2020Q2", "2020Q4", freq="Q") else 1.0
        market = (
            2.05e6 * (population_m / 31.2) * (income_idx / 100) ** 0.6
            * season * covid * (1 + 0.07 * fiveg)
        )
        promo_intensity = round(float(np.clip(rng.normal(0.5 + 0.2 * (q.quarter == 4), 0.12), 0, 1)), 2)
        for brand, (share, drift, price) in BRANDS.items():
            s = max(0.02, share + drift * t)
            launch_boost = 1.08 if (brand in ("Samsung", "Apple") and q.quarter in (1, 3)) else 1.0
            units = market * s * launch_boost * (1 + 0.10 * (promo_intensity - 0.5))
            units *= rng.normal(1, 0.035)
            avg_price = price * (1.025 ** t) * rng.normal(1, 0.02)
            rows.append({
                "quarter": str(q),
                "year": q.year,
                "q": q.quarter,
                "brand": brand,
                "units_sold": int(units),
                "avg_price_myr": round(avg_price, 0),
                "population_m": round(population_m, 2),
                "income_index": round(income_idx, 1),
                "promo_intensity": promo_intensity,
                "is_5g_era": int(fiveg),
            })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    main()

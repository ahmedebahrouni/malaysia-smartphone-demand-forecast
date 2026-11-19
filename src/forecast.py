"""
Forecast quarterly smartphone unit sales in Malaysia by brand, 2026-2028.

Pipeline
1. Load data and engineer features (trend, quarter seasonality, lags, macro drivers)
2. Backtest two models on 2024-2025 (holdout): seasonal-naive baseline vs. Gradient Boosting
3. Refit on all history and forecast 12 quarters ahead, recursively, per brand
4. Export tidy CSVs for Power BI and charts for the README
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error

DATA = "data/malaysia_smartphone_sales.csv"
OUT = "outputs"
FEATURES = ["t", "q1", "q2", "q3", "q4", "lag_4", "lag_1", "income_index",
            "population_m", "promo_intensity", "is_5g_era", "brand_code"]
HORIZON = pd.period_range("2026Q1", "2028Q4", freq="Q")


def add_features(df):
    df = df.sort_values(["brand", "quarter"]).copy()
    df["t"] = (df["year"] - 2016) * 4 + df["q"] - 1
    for k in range(1, 5):
        df[f"q{k}"] = (df["q"] == k).astype(int)
    df["lag_1"] = df.groupby("brand")["units_sold"].shift(1)
    df["lag_4"] = df.groupby("brand")["units_sold"].shift(4)
    df["brand_code"] = df["brand"].astype("category").cat.codes
    return df


def model():
    return GradientBoostingRegressor(n_estimators=400, max_depth=3,
                                     learning_rate=0.05, subsample=0.9, random_state=0)


def backtest(df):
    train = df[(df["year"] < 2024)].dropna(subset=["lag_4"])
    test = df[df["year"] >= 2024]
    m = model().fit(train[FEATURES], train["units_sold"])
    pred = m.predict(test[FEATURES])
    naive = test["lag_4"]  # same quarter last year
    res = {
        "Seasonal naive (same quarter last year)": mean_absolute_percentage_error(test["units_sold"], naive),
        "Gradient Boosting": mean_absolute_percentage_error(test["units_sold"], pred),
    }
    return res, m


def forecast(df):
    hist = df.dropna(subset=["lag_4"])
    m = model().fit(hist[FEATURES], hist["units_sold"])
    codes = dict(zip(df["brand"], df["brand_code"]))
    last = df[df["quarter"] == "2025Q4"].set_index("brand")
    series = {b: list(df[df["brand"] == b].sort_values("quarter")["units_sold"]) for b in codes}
    trend = {b: float(np.mean([s[-k] / s[-k - 4] for k in range(1, 9)])) for b, s in series.items()}
    out = []
    for i, p in enumerate(HORIZON, start=1):
        for b, code in codes.items():
            years_ahead = i / 4
            x = {
                "t": (p.year - 2016) * 4 + p.quarter - 1,
                **{f"q{k}": int(p.quarter == k) for k in range(1, 5)},
                "lag_1": series[b][-1], "lag_4": series[b][-4],
                # macro assumptions: income +3.5%/yr, population +1.1%/yr, average promos
                "income_index": last.loc[b, "income_index"] * 1.035 ** years_ahead,
                "population_m": last.loc[b, "population_m"] * 1.011 ** years_ahead,
                "promo_intensity": 0.7 if p.quarter == 4 else 0.5,
                "is_5g_era": 1, "brand_code": code,
            }
            y_model = float(m.predict(pd.DataFrame([x])[FEATURES])[0])
            # Tree models can't extrapolate a trend, so blend with a seasonal-trend
            # estimate: same quarter last year x the brand's average YoY growth
            # over the last 8 actual quarters.
            y_trend = series[b][-4] * trend[b]
            y = 0.5 * y_model + 0.5 * y_trend
            series[b].append(y)
            out.append({"quarter": str(p), "year": p.year, "brand": b, "units_forecast": int(y)})
    return pd.DataFrame(out)


def charts(df, fc):
    tot = df.groupby("quarter")["units_sold"].sum()
    ftot = fc.groupby("quarter")["units_forecast"].sum()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(tot.index, tot.values / 1e6, label="Actual (simulated)")
    ax.plot(ftot.index, ftot.values / 1e6, "--", label="Forecast")
    ax.set_ylabel("Units (millions)")
    ax.set_title("Malaysia smartphone units per quarter")
    ax.set_xticks(list(tot.index[::4]) + list(ftot.index[::4]))
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT}/total_market_forecast.png", dpi=150)

    sam = df[df["brand"] == "Samsung"].set_index("quarter")["units_sold"]
    fsam = fc[fc["brand"] == "Samsung"].set_index("quarter")["units_forecast"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(sam.index, sam.values / 1e3, label="Actual (simulated)")
    ax.plot(fsam.index, fsam.values / 1e3, "--", label="Forecast")
    ax.set_ylabel("Units (thousands)")
    ax.set_title("Samsung units per quarter, Malaysia")
    ax.set_xticks(list(sam.index[::4]) + list(fsam.index[::4]))
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT}/samsung_forecast.png", dpi=150)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = add_features(pd.read_csv(DATA))
    scores, _ = backtest(df)
    print("Backtest MAPE on 2024-2025 holdout:")
    for k, v in scores.items():
        print(f"  {k}: {v:.1%}")
    fc = forecast(df)
    fc.to_csv(f"{OUT}/forecast_2026_2028.csv", index=False)

    yearly = pd.concat([
        df.groupby(["year", "brand"])["units_sold"].sum().rename("units"),
        fc.groupby(["year", "brand"])["units_forecast"].sum().rename("units"),
    ]).reset_index()
    yearly["type"] = np.where(yearly["year"] >= 2026, "forecast", "actual")
    yearly.to_csv(f"{OUT}/yearly_by_brand.csv", index=False)
    pivot = yearly[yearly["year"] >= 2023].pivot(index="year", columns="brand", values="units")
    pivot["Total"] = pivot.sum(axis=1)
    print("\nUnits per year (2023-2025 actual, 2026-2028 forecast):")
    print((pivot / 1e6).round(2).to_string())
    share = (pivot.drop(columns="Total").div(pivot["Total"], axis=0) * 100).round(1)
    print("\nMarket share %:")
    print(share.to_string())
    charts(df, fc)


if __name__ == "__main__":
    main()

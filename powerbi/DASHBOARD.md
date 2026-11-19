# Power BI dashboard: Malaysia Smartphone Demand

## Data model (star schema)
- **FactSales**: `data/malaysia_smartphone_sales.csv` (quarter, brand, units_sold, avg_price_myr, promo_intensity)
- **FactForecast**: `outputs/forecast_2026_2028.csv` (quarter, brand, units_forecast)
- **DimBrand**: Brand
- **DimDate**: Quarter, Year, QuarterNumber

Relationships: DimBrand[Brand] 1→* both fact tables; DimDate[Quarter] 1→* both fact tables.

## DAX measures
```DAX
Units Actual = SUM ( FactSales[units_sold] )

Units Forecast = SUM ( FactForecast[units_forecast] )

Units (Actual + Forecast) = [Units Actual] + [Units Forecast]

Revenue MYR = SUMX ( FactSales, FactSales[units_sold] * FactSales[avg_price_myr] )

Market Share % =
DIVIDE ( [Units (Actual + Forecast)],
         CALCULATE ( [Units (Actual + Forecast)], ALL ( DimBrand ) ) )

YoY Growth % =
VAR PrevYear = CALCULATE ( [Units (Actual + Forecast)],
                           DimDate[Year] = MAX ( DimDate[Year] ) - 1,
                           ALL ( DimDate ) )
RETURN DIVIDE ( [Units (Actual + Forecast)] - PrevYear, PrevYear )
```

## Pages
1. **Market overview**: KPI cards (units in 2025, forecast for 2028, CAGR), a line chart of actual vs forecast, and a brand slicer
2. **Brand battle**: a 100% stacked column chart of market share by year, plus a table of YoY growth by brand
3. **Seasonality**: a units-by-quarter heatmap (Year × Q) and promo intensity vs units
4. **Samsung deep dive**: Samsung units, share and revenue trend, with forecast bands

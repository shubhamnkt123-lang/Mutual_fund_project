"""
Mutual Fund Overview & Insights — Data Analytics Project
==========================================================
Stages covered: Data Cleaning -> Description -> Normalization ->
                 Scoring & Ranking -> Top 30 Export -> Summary Tables

Input : comprehensive_mutual_funds_data.csv (814 rows x 20 columns)
Output: cleaned_data.csv, statistics.csv, missing_values.csv,
        category_summary.csv, subcategory_summary.csv, amc_summary.csv,
        manager_summary.csv, top30.csv, scored_full.csv
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

pd.set_option("display.width", 140)
RAW_PATH = "comprehensive_mutual_funds_data.csv"
raw = pd.read_csv(RAW_PATH)
df = raw.copy()
RATIO_COLS = ["sortino", "alpha", "sd", "beta", "sharpe"]
for c in RATIO_COLS:
    df[c] = pd.to_numeric(df[c].replace("-", np.nan), errors="coerce")
df["scheme_name"] = df["scheme_name"].str.strip()
missing_count = df.isnull().sum()
missing_pct = df.isnull().mean() * 100
missing_values = pd.DataFrame({"Column": df.columns, "Missing Count": missing_count.values, "Missing %": missing_pct.values})
df.to_csv("cleaned_data.csv", index=False)
missing_values.to_csv("missing_values.csv", index=False)

NUMERIC_FIELDS = ["min_sip", "min_lumpsum", "expense_ratio", "fund_size_cr", "fund_age_yr", "risk_level", "rating", "returns_1yr", "returns_3yr", "returns_5yr"]
stat_rows = []
for f in NUMERIC_FIELDS:
    s = df[f].dropna()
    mode_val = s.mode().iloc[0] if not s.mode().empty else np.nan
    stat_rows.append({"Field": f, "Count": int(s.count()), "Mean": s.mean(), "Median": s.median(), "Mode": mode_val, "Min": s.min(), "Max": s.max(), "Std Dev": s.std(), "Skewness": s.skew()})
statistics = pd.DataFrame(stat_rows)
statistics.to_csv("statistics.csv", index=False)

score_df = df[df["returns_3yr"].notna()].copy()
scaler = MinMaxScaler()
score_df["return_3yr_norm"] = scaler.fit_transform(score_df[["returns_3yr"]])
score_df["risk_score"] = 1 - scaler.fit_transform(score_df[["risk_level"]])
score_df["expense_score"] = 1 - scaler.fit_transform(score_df[["expense_ratio"]])
SWEET_SPOT_YEARS = 7.5
age_distance = (score_df["fund_age_yr"] - SWEET_SPOT_YEARS).abs()
score_df["age_score"] = 1 - scaler.fit_transform(age_distance.to_frame())
score_df["positive_1yr_score"] = (score_df["returns_1yr"] > 0).astype(int)
W_RETURN, W_RISK, W_EXPENSE, W_AGE, W_CONSISTENCY = 0.35, 0.25, 0.20, 0.10, 0.10
score_df["overall_score"] = 100 * (W_RETURN * score_df["return_3yr_norm"] + W_RISK * score_df["risk_score"] + W_EXPENSE * score_df["expense_score"] + W_AGE * score_df["age_score"] + W_CONSISTENCY * score_df["positive_1yr_score"])
score_df = score_df.sort_values("overall_score", ascending=False).reset_index(drop=True)
score_df.insert(0, "rank", score_df.index + 1)
score_df.to_csv("scored_full.csv", index=False)
COLS_ORDER = ["rank", "scheme_name", "min_sip", "min_lumpsum", "expense_ratio", "fund_size_cr", "fund_age_yr", "fund_manager", "sortino", "alpha", "sd", "beta", "sharpe", "risk_level", "amc_name", "rating", "category", "sub_category", "returns_1yr", "returns_3yr", "returns_5yr", "return_3yr_norm", "risk_score", "expense_score", "age_score", "positive_1yr_score", "overall_score"]
top30 = score_df.head(30)[COLS_ORDER]
top30.to_csv("top30.csv", index=False)

category_summary = df.groupby("category").agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"), avg_expense_ratio=("expense_ratio", "mean"), avg_returns_1yr=("returns_1yr", "mean"), avg_returns_3yr=("returns_3yr", "mean"), avg_risk_level=("risk_level", "mean")).reset_index().sort_values("total_aum_cr", ascending=False)
category_summary.to_csv("category_summary.csv", index=False)
subcategory_summary = df.groupby(["category", "sub_category"]).agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"), avg_expense_ratio=("expense_ratio", "mean"), avg_returns_3yr=("returns_3yr", "mean")).reset_index().sort_values(["category", "total_aum_cr"], ascending=[True, False])
subcategory_summary.to_csv("subcategory_summary.csv", index=False)
amc_summary = df.groupby("amc_name").agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"), avg_returns_3yr=("returns_3yr", "mean")).reset_index().sort_values("total_aum_cr", ascending=False)
amc_summary.to_csv("amc_summary.csv", index=False)
manager_summary = df.groupby("fund_manager").agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum")).reset_index().sort_values("total_aum_cr", ascending=False)
manager_summary.to_csv("manager_summary.csv", index=False)
print("Done. Analysis outputs generated.")

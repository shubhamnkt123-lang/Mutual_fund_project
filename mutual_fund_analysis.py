"""
Mutual Fund Overview & Insights — Data Analytics Project
==========================================================
Stages covered: Data Cleaning -> Description -> Normalization ->
                 Scoring & Ranking -> Top 30 Export -> Summary Tables

Input : comprehensive_mutual_funds_data.csv (814 rows x 20 columns)
Output: cleaned_data.csv, statistics.csv, missing_values.csv,
        category_summary.csv, subcategory_summary.csv, amc_summary.csv,
        manager_summary.csv, top30.csv, scored_full.csv
        (these feed directly into the sheets of Mutual_Fund_Analysis.xlsx)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

pd.set_option("display.width", 140)

# ----------------------------------------------------------------------
# STAGE 1 — DATA CLEANING
# ----------------------------------------------------------------------
RAW_PATH = "comprehensive_mutual_funds_data.csv"

raw = pd.read_csv(RAW_PATH)
print("RAW SHAPE:", raw.shape)
df = raw.copy()

# The five risk-ratio columns (sortino, alpha, sd, beta, sharpe) load as TEXT
# because missing values are encoded as the literal string "-" instead of a
# blank cell. Convert "-" -> NaN, then cast to float so they behave as numbers.
RATIO_COLS = ["sortino", "alpha", "sd", "beta", "sharpe"]
for c in RATIO_COLS:
    df[c] = pd.to_numeric(df[c].replace("-", np.nan), errors="coerce")

df["scheme_name"] = df["scheme_name"].str.strip()

# Missing-value strategy: genuine gaps are LEFT AS NaN rather than imputed.
# returns_3yr is a required scoring input, so rows missing it are excluded
# from the ranking step later (Stage 4) instead of being filled with a
# guessed value. returns_5yr is not a scoring input and is kept as-is for
# reference (many funds are simply too young to have a 5-year track record).
missing_count = df.isnull().sum()
missing_pct = df.isnull().mean() * 100
missing_values = pd.DataFrame(
    {"Column": df.columns, "Missing Count": missing_count.values, "Missing %": missing_pct.values}
)
print("\nMISSING VALUES:\n", missing_values[missing_values["Missing Count"] > 0])

df.to_csv("cleaned_data.csv", index=False)
missing_values.to_csv("missing_values.csv", index=False)
print("\nSaved -> cleaned_data.csv, missing_values.csv")

# ----------------------------------------------------------------------
# STAGE 2 — DATA DESCRIPTION & UNDERSTANDING
# ----------------------------------------------------------------------
NUMERIC_FIELDS = [
    "min_sip", "min_lumpsum", "expense_ratio", "fund_size_cr", "fund_age_yr",
    "risk_level", "rating", "returns_1yr", "returns_3yr", "returns_5yr",
]

stat_rows = []
for f in NUMERIC_FIELDS:
    s = df[f].dropna()
    mode_val = s.mode().iloc[0] if not s.mode().empty else np.nan
    stat_rows.append({
        "Field": f, "Count": int(s.count()), "Mean": s.mean(), "Median": s.median(),
        "Mode": mode_val, "Min": s.min(), "Max": s.max(),
        "Std Dev": s.std(), "Skewness": s.skew(),
    })
statistics = pd.DataFrame(stat_rows)
statistics.to_csv("statistics.csv", index=False)
print("\nSTATISTICS:\n", statistics)

# Notable outlier check (Stage 2, Q3): a single Debt-category fund posts a
# 130.8% one-year return, far outside the Debt category's normal range
# (average ~6% over three years) — most plausibly a one-off NAV recovery,
# not a repeatable pattern. Flagged here, not deleted.
outlier = df.loc[df["returns_1yr"].idxmax()]
print(f"\nOutlier check — highest 1yr return: {outlier['scheme_name']} "
      f"({outlier['category']}) at {outlier['returns_1yr']}%")

# ----------------------------------------------------------------------
# STAGE 3 — NORMALIZATION
# ----------------------------------------------------------------------
# Only rows with a valid 3-year return are eligible for scoring/ranking.
score_df = df[df["returns_3yr"].notna()].copy()
scaler = MinMaxScaler()

score_df["return_3yr_norm"] = scaler.fit_transform(score_df[["returns_3yr"]])
score_df["risk_score"] = 1 - scaler.fit_transform(score_df[["risk_level"]])       # lower risk -> higher score
score_df["expense_score"] = 1 - scaler.fit_transform(score_df[["expense_ratio"]])  # lower expense -> higher score

SWEET_SPOT_YEARS = 7.5
age_distance = (score_df["fund_age_yr"] - SWEET_SPOT_YEARS).abs()
score_df["age_score"] = 1 - scaler.fit_transform(age_distance.to_frame())
score_df["positive_1yr_score"] = (score_df["returns_1yr"] > 0).astype(int)

# ----------------------------------------------------------------------
# STAGE 4 — FUND SCORING & RANKING
# ----------------------------------------------------------------------
# Score = 100 x [0.35 x 3Yr Return(norm) + 0.25 x Low Risk(norm, inverted)
#              + 0.20 x Low Expense(norm, inverted) + 0.10 x Moderate Age(norm)
#              + 0.10 x Positive 1Yr Return(flag)]
W_RETURN, W_RISK, W_EXPENSE, W_AGE, W_CONSISTENCY = 0.35, 0.25, 0.20, 0.10, 0.10

score_df["overall_score"] = 100 * (
    W_RETURN * score_df["return_3yr_norm"]
    + W_RISK * score_df["risk_score"]
    + W_EXPENSE * score_df["expense_score"]
    + W_AGE * score_df["age_score"]
    + W_CONSISTENCY * score_df["positive_1yr_score"]
)

score_df = score_df.sort_values("overall_score", ascending=False).reset_index(drop=True)
score_df.insert(0, "rank", score_df.index + 1)
score_df.to_csv("scored_full.csv", index=False)
print(f"\nScored {len(score_df)} funds (21 funds without a 3yr return were excluded).")

# ----------------------------------------------------------------------
# STAGE 5 — TOP 30 EXPORT
# ----------------------------------------------------------------------
COLS_ORDER = [
    "rank", "scheme_name", "min_sip", "min_lumpsum", "expense_ratio", "fund_size_cr",
    "fund_age_yr", "fund_manager", "sortino", "alpha", "sd", "beta", "sharpe",
    "risk_level", "amc_name", "rating", "category", "sub_category",
    "returns_1yr", "returns_3yr", "returns_5yr",
    "return_3yr_norm", "risk_score", "expense_score", "age_score",
    "positive_1yr_score", "overall_score",
]
top30 = score_df.head(30)[COLS_ORDER]
top30.to_csv("top30.csv", index=False)
print("\nTOP 30 preview:\n", top30[["rank", "scheme_name", "category", "overall_score"]].head(10))
print("\nTop 30 category mix:\n", top30["category"].value_counts())
print("Top 30 funds at risk level 1-2:", (top30["risk_level"] <= 2).sum(), "of 30")

# ----------------------------------------------------------------------
# SUMMARY TABLES (feed the dashboard / Excel summary sheets)
# ----------------------------------------------------------------------
category_summary = (
    df.groupby("category")
    .agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"),
         avg_expense_ratio=("expense_ratio", "mean"), avg_returns_1yr=("returns_1yr", "mean"),
         avg_returns_3yr=("returns_3yr", "mean"), avg_risk_level=("risk_level", "mean"))
    .reset_index().sort_values("total_aum_cr", ascending=False)
)
category_summary.to_csv("category_summary.csv", index=False)

subcategory_summary = (
    df.groupby(["category", "sub_category"])
    .agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"),
         avg_expense_ratio=("expense_ratio", "mean"), avg_returns_3yr=("returns_3yr", "mean"))
    .reset_index().sort_values(["category", "total_aum_cr"], ascending=[True, False])
)
subcategory_summary.to_csv("subcategory_summary.csv", index=False)

amc_summary = (
    df.groupby("amc_name")
    .agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"),
         avg_returns_3yr=("returns_3yr", "mean"))
    .reset_index().sort_values("total_aum_cr", ascending=False)
)
amc_summary.to_csv("amc_summary.csv", index=False)

manager_summary = (
    df.groupby("fund_manager")
    .agg(schemes=("scheme_name", "count"), total_aum_cr=("fund_size_cr", "sum"))
    .reset_index().sort_values("total_aum_cr", ascending=False)
)
manager_summary.to_csv("manager_summary.csv", index=False)

print("\nSaved -> statistics.csv, category_summary.csv, subcategory_summary.csv,")
print("         amc_summary.csv, manager_summary.csv, top30.csv, scored_full.csv")
print("\nDone. These CSVs are the same data behind Mutual_Fund_Analysis.xlsx.")

# Mutual Fund Overview & Insights — Project Write-Up

**Dataset:** `comprehensive_mutual_funds_data.csv` — 814 mutual fund schemes × 20 columns
**Tools:** Python (Pandas, scikit-learn) → Excel (`Mutual_Fund_Analysis.xlsx`) → Interactive Dashboard

---

## Stage 0 — Goal & Problem Statement

**Goal.** Identify mutual fund schemes with a strong return/risk/cost balance, shortlist the Top 30, and communicate the findings in a way a non-technical, first-time investor can act on.

**Why balance return and risk?** A very high-return fund can also carry high risk or high cost. Ranking by return alone favours volatile or expensive funds — for example, the single highest 1-year return in this dataset (130.8%) comes from a *Debt*-category fund, a category that normally averages ~6% over three years. That number is almost certainly a one-off NAV recovery, not a repeatable skill — exactly the kind of pick a return-only ranking would wrongly reward.

**Objectives.** Clean the data → explore patterns → normalise metrics → build a transparent weighted score → rank funds → export the Top 30 → build an interactive dashboard.

**Tool roles.** Python handles cleaning, EDA, normalisation, and scoring — the statistical work needs to be reproducible and auditable. Excel packages the Top 30 into a portable, shareable format. The dashboard turns the ranked data into an explorable story with filters and KPIs for a non-technical audience.

---

## Stage 1 — Data Cleaning

- **Shape:** 814 rows × 20 columns. *(Note: the brief describes 2,500+ schemes; the supplied file contains 814 — this analysis uses the supplied file as-is.)*
- **Numeric standardisation:** `sortino`, `alpha`, `sd`, `beta`, and `sharpe` loaded as text because missing values used the placeholder `"-"` instead of a blank cell — one non-numeric string is enough to force a whole column to string dtype. Fixed by replacing `"-"` with `NaN` and casting to float.
- **Missing values:**

| Field | Missing | % |
|---|---|---|
| `returns_3yr` | 21 | 2.58% |
| `returns_5yr` | 167 | 20.52% |
| `sortino`, `sharpe` | 23 each | 2.83% |
| `alpha`, `beta` | 42 each | 5.16% |

Rows missing `returns_3yr` (a required scoring input) are **excluded from ranking** rather than imputed, to avoid guessing a value for the formula's most heavily weighted input. `returns_5yr` isn't a scoring input and is left as genuine missing data (many funds are simply too young for a 5-year history).

---

## Stage 2 — Data Description

Descriptive statistics (mean, median, mode, min, max, std dev, skewness) were computed for all 10 numeric fields — see `statistics.csv`. Highlights: median expense ratio is 0.615%, median fund age is 10 years, and `returns_1yr` is heavily right-skewed (skewness ≈ 8.4) driven almost entirely by the Bank of India Credit Risk Fund outlier at 130.8%.

---

## Stage 3 — Normalization

`MinMaxScaler` was applied to `returns_3yr`, `risk_level`, and `expense_ratio`, scaling each to a common 0–1 range. Because higher `returns_3yr` is better but lower `risk_level` and `expense_ratio` are better, the risk and expense scores are **inverted** (`1 − scaled_value`) so every term in the final formula means the same thing: "higher = better for the investor." `fund_age_yr` is scored differently — not maximised, but scored for **closeness to a 7.5-year sweet spot**, since both brand-new funds (no track record) and unusually old funds are less desirable than a fund with a proven, moderate history.

---

## Stage 4 — Fund Scoring & Ranking

```
Score = 100 x [ 0.35 x 3Yr Return (normalized)
              + 0.25 x Low Risk (normalized, inverted)
              + 0.20 x Low Expense (normalized, inverted)
              + 0.10 x Moderate Age (normalized)
              + 0.10 x Positive 1Yr Return (flag: 1 if >0, else 0) ]
```

Return carries the largest weight because it's the primary reason to invest at all; risk is weighted second-highest because the brief's core premise is that risk must be actively controlled, not just noted; expense ratio is a smaller but still meaningful recurring cost; age and 1-year consistency act as secondary sense-checks rather than primary drivers. All 793 funds with a valid 3-year return were scored and ranked.

---

## Stage 5 — Top 30 Shortlist

- **Category mix:** Debt 21, Hybrid 5, Equity 4.
- **Risk profile:** 27 of the 30 shortlisted funds sit at risk level 1–2 (Low / Low-Moderate) — the 25% weight on low risk visibly pulls the shortlist toward stable, lower-volatility schemes rather than pure high-return chasers, which is the intended effect given Stage 0's premise.
- **Rank #1:** the top-scoring fund combines a strong 3-year return with very low risk level and a low expense ratio — the formula's four factors are all pulling in the same direction for it, not just one.

---

## Stage 7 — Insights (figures from the cleaned dataset)

1. **Largest AUM category:** Equity — ₹13,54,231.74 crore, **43.6%** of total dataset AUM.
2. **Highest-AUM fund manager:** Rahul Goswami — ₹1,31,306 crore across 8 schemes.
3. **Lowest expense ratio:** Debt category overall (0.36% average); Fixed Maturity Plans is the cheapest sub-category (0.045% average).
4. **Best 1-year return:** Bank of India Credit Risk Fund at 130.8% — flagged in Stage 2 as an outlier, and specifically why 1-year return is used only as a consistency *flag* in the scoring formula, not the primary driver.
5. **SIP / lump-sum:** average minimum SIP ₹528.50; median minimum lump-sum ₹5,000 (average ₹3,047.47).
6. **3-year return by category:** Equity 29.7% → Other 20.8% → Solution Oriented 18.2% → Hybrid 15.3% → Debt 6.2%. Return climbs with category risk level almost monotonically — the trade-off from Stage 0 is visible directly in the data.

**Final reflection.** For a first-time investor wanting low-risk, steady growth, the Top 30 shortlist itself already leans toward Debt and Hybrid schemes rather than the highest-return Equity funds — a direct result of weighting risk at 25% in the formula. Python made this process reproducible and auditable, Excel made the result portable to a non-technical reader, and the dashboard turns the numbers into something explorable rather than a static list — together producing a shortlist that traces back to the data at every step, not a guess.

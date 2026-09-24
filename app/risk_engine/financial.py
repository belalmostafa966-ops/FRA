from typing import Dict, Any, Tuple, List
from config import EWS_THRESHOLDS

def calculate_financial_ratios(
    revenue: float,
    net_income: float,
    total_assets: float,
    total_liabilities: float,
    current_assets: float,
    current_liabilities: float,
    total_equity: float,
    cash_and_equivalents: float
) -> Dict[str, float]:
    """
    Computes key financial ratios safely avoiding ZeroDivisionError.
    """
    # 1. Profit Margin = Net Income / Revenue
    profit_margin = (net_income / revenue) if revenue and revenue != 0 else (0.0 if net_income >= 0 else -1.0)

    # 2. Debt Ratio = Total Liabilities / Total Assets
    debt_ratio = (total_liabilities / total_assets) if total_assets and total_assets > 0 else 0.0

    # 3. Debt to Equity = Total Liabilities / Total Equity
    debt_to_equity = (total_liabilities / total_equity) if total_equity and total_equity > 0 else (10.0 if total_liabilities > 0 else 0.0)

    # 4. Liability Ratio = Total Liabilities / Total Assets (or Total Equity)
    liability_ratio = debt_ratio

    # 5. Current Ratio = Current Assets / Current Liabilities
    current_ratio = (current_assets / current_liabilities) if current_liabilities and current_liabilities > 0 else (5.0 if current_assets > 0 else 0.0)

    # 6. Cash Ratio = Cash & Equivalents / Current Liabilities
    cash_ratio = (cash_and_equivalents / current_liabilities) if current_liabilities and current_liabilities > 0 else (2.0 if cash_and_equivalents > 0 else 0.0)

    return {
        "profit_margin": round(profit_margin, 4),
        "debt_ratio": round(debt_ratio, 4),
        "liability_ratio": round(liability_ratio, 4),
        "debt_to_equity": round(debt_to_equity, 4),
        "current_ratio": round(current_ratio, 4),
        "cash_ratio": round(cash_ratio, 4),
    }

def calculate_financial_risk_score(ratios: Dict[str, float]) -> float:
    """
    Computes Financial Risk Score (0-100 scale).
    Higher score indicates higher risk level.
    """
    # Profit Margin risk component: PM >= 15% -> 0 risk, PM <= -20% -> 100 risk
    pm = ratios["profit_margin"]
    if pm >= 0.15:
        pm_risk = 0.0
    elif pm <= -0.20:
        pm_risk = 100.0
    else:
        pm_risk = (0.15 - pm) / 0.35 * 100.0

    # Debt Ratio risk component: DR <= 0.40 -> 0 risk, DR >= 0.85 -> 100 risk
    dr = ratios["debt_ratio"]
    if dr <= 0.40:
        dr_risk = 0.0
    elif dr >= 0.85:
        dr_risk = 100.0
    else:
        dr_risk = (dr - 0.40) / 0.45 * 100.0

    # Debt-to-Equity risk component: D/E <= 1.5 -> 0 risk, D/E >= 5.0 -> 100 risk
    de = ratios["debt_to_equity"]
    if de <= 1.5:
        de_risk = 0.0
    elif de >= 5.0:
        de_risk = 100.0
    else:
        de_risk = (de - 1.5) / 3.5 * 100.0

    # Current Ratio risk component: CR >= 1.5 -> 0 risk, CR <= 0.5 -> 100 risk
    cr = ratios["current_ratio"]
    if cr >= 1.5:
        cr_risk = 0.0
    elif cr <= 0.5:
        cr_risk = 100.0
    else:
        cr_risk = (1.5 - cr) / 1.0 * 100.0

    # Cash Ratio risk component: CashR >= 0.5 -> 0 risk, CashR <= 0.05 -> 100 risk
    cash_r = ratios["cash_ratio"]
    if cash_r >= 0.50:
        cash_risk = 0.0
    elif cash_r <= 0.05:
        cash_risk = 100.0
    else:
        cash_risk = (0.50 - cash_r) / 0.45 * 100.0

    # Weighted Financial Score
    fin_score = (
        0.25 * pm_risk +
        0.25 * dr_risk +
        0.20 * de_risk +
        0.15 * cr_risk +
        0.15 * cash_risk
    )

    return round(min(100.0, max(0.0, fin_score)), 2)

def calculate_composite_risk(
    complaints_score: float,
    financial_score: float,
    complaint_weight: float = 0.50,
    financial_weight: float = 0.50
) -> Tuple[float, str]:
    """
    Computes blended composite risk score (0-100) and categorizes risk level.
    Returns (composite_score, risk_level).
    """
    total_w = complaint_weight + financial_weight
    cw = complaint_weight / total_w
    fw = financial_weight / total_w

    composite = cw * complaints_score + fw * financial_score
    composite = round(min(100.0, max(0.0, composite)), 2)

    if composite >= 75.0:
        risk_level = "Critical"
    elif composite >= 55.0:
        risk_level = "High"
    elif composite >= 30.0:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return composite, risk_level

def evaluate_financial_ews_alerts(
    ratios: Dict[str, float],
    financial_score: float
) -> Tuple[bool, List[str]]:
    """
    Generates Early Warning System (EWS) triggers for financial metrics.
    """
    reasons = []

    if financial_score >= EWS_THRESHOLDS["FINANCIAL_SCORE_CRITICAL"]:
        reasons.append(f"Critical Financial Risk Score ({financial_score:.1f} / 100)")
    elif financial_score >= EWS_THRESHOLDS["FINANCIAL_SCORE_HIGH"]:
        reasons.append(f"High Financial Risk Score ({financial_score:.1f} / 100)")

    if ratios["profit_margin"] < -0.10:
        reasons.append(f"Severe Loss Margin ({ratios['profit_margin']*100:.1f}%)")

    if ratios["current_ratio"] < 0.8:
        reasons.append(f"Liquidity Stress: Current Ratio is {ratios['current_ratio']:.2f} (< 1.0)")

    if ratios["debt_ratio"] > 0.80:
        reasons.append(f"Extreme Solvency Risk: Debt Ratio is {ratios['debt_ratio']*100:.1f}%")

    return len(reasons) > 0, reasons

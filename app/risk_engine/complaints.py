from typing import Dict, Any, List, Tuple
from config import DEFAULT_COMPLAINT_WEIGHTS, EWS_THRESHOLDS

def calculate_complaints_metrics(
    total_complaints: int,
    negative_count: int,
    high_severity_count: int,
    open_count: int,
    fraud_allegation_count: int,
    growth_rate: float,
    benchmark_max_volume: int = 500
) -> Dict[str, float]:
    """
    Computes key complaint ratios and normalized risk components (0-100).
    Safely handles zero-division.
    """
    total = max(0, total_complaints)
    
    if total == 0:
        negative_ratio = 0.0
        high_severity_ratio = 0.0
        open_ratio = 0.0
        fraud_ratio = 0.0
        volume_norm = 0.0
    else:
        negative_ratio = min(1.0, max(0.0, negative_count / total))
        high_severity_ratio = min(1.0, max(0.0, high_severity_count / total))
        open_ratio = min(1.0, max(0.0, open_count / total))
        fraud_ratio = min(1.0, max(0.0, fraud_allegation_count / total))
        volume_norm = min(1.0, total / max(1, benchmark_max_volume))

    # Normalized scores (0 - 100 scale)
    vol_score = volume_norm * 100.0
    neg_score = negative_ratio * 100.0
    sev_score = high_severity_ratio * 100.0
    open_score = open_ratio * 100.0
    fraud_score = fraud_ratio * 100.0
    
    # Growth score: positive growth indicates increasing risk. Map 0% growth to 30 score, 50% growth to 100 score.
    clamped_growth = max(-0.5, min(1.5, growth_rate))
    if clamped_growth <= 0:
        growth_score = max(0.0, (1.0 + clamped_growth) * 30.0)
    else:
        growth_score = min(100.0, 30.0 + clamped_growth * 140.0)

    return {
        "negative_ratio": negative_ratio,
        "high_severity_ratio": high_severity_ratio,
        "open_ratio": open_ratio,
        "fraud_ratio": fraud_ratio,
        "growth_rate": growth_rate,
        "vol_score": vol_score,
        "neg_score": neg_score,
        "sev_score": sev_score,
        "open_score": open_score,
        "fraud_score": fraud_score,
        "growth_score": growth_score,
    }

def calculate_complaints_risk_score(
    metrics: Dict[str, float],
    weights: Dict[str, float] = None
) -> float:
    """
    Calculates weighted Complaints Risk Score (0-100).
    Score = w_vol*(Volume) + w_neg*(Negative) + w_sev*(Severity) + w_open*(Open) + w_fraud*(Fraud) + w_growth*(Growth)
    """
    if weights is None:
        weights = DEFAULT_COMPLAINT_WEIGHTS

    # Ensure weights are normalized to sum to 1.0
    total_w = sum(weights.values())
    if total_w <= 0:
        w_norm = DEFAULT_COMPLAINT_WEIGHTS
    else:
        w_norm = {k: v / total_w for k, v in weights.items()}

    score = (
        w_norm.get("vol_w", 0.20) * metrics["vol_score"] +
        w_norm.get("neg_w", 0.20) * metrics["neg_score"] +
        w_norm.get("sev_w", 0.20) * metrics["sev_score"] +
        w_norm.get("open_w", 0.15) * metrics["open_score"] +
        w_norm.get("fraud_w", 0.10) * metrics["fraud_score"] +
        w_norm.get("growth_w", 0.15) * metrics["growth_score"]
    )

    return round(min(100.0, max(0.0, score)), 2)

def evaluate_complaint_ews_alerts(
    metrics: Dict[str, float],
    complaint_score: float
) -> Tuple[bool, List[str]]:
    """
    Generates Early Warning System (EWS) triggers based on risk thresholds.
    """
    reasons = []
    
    if complaint_score >= EWS_THRESHOLDS["COMPLAINT_SCORE_CRITICAL"]:
        reasons.append(f"Critical Complaints Risk Score ({complaint_score:.1f} / 100)")
    elif complaint_score >= EWS_THRESHOLDS["COMPLAINT_SCORE_HIGH"]:
        reasons.append(f"High Complaints Risk Score ({complaint_score:.1f} / 100)")

    if metrics["fraud_ratio"] >= EWS_THRESHOLDS["FRAUD_RATIO_HIGH"]:
        reasons.append(f"Elevated Fraud Allegations ({metrics['fraud_ratio']*100:.1f}% of complaints)")

    if metrics["growth_rate"] >= EWS_THRESHOLDS["GROWTH_RATE_SPIKE"]:
        reasons.append(f"Surge in Complaint Volume (+{metrics['growth_rate']*100:.1f}% QoQ)")

    if metrics["open_ratio"] >= 0.40:
        reasons.append(f"High Unresolved Complaints Ratio ({metrics['open_ratio']*100:.1f}%)")

    alert_flag = len(reasons) > 0
    return alert_flag, reasons

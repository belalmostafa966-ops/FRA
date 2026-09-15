// overallRisk.js
// Combines complaint risk + financial risk into one overall score

function getOverallRiskLevel(score) {
  if (score >= 85) return 'Critical';
  if (score >= 70) return 'High';
  if (score >= 40) return 'Medium';
  return 'Low';
}

function calculateOverallRisk(complaintResult, financialResult) {
  const complaintScore = complaintResult.complaint_risk_score ?? 0;
  const financialScore = financialResult.financial_risk_score ?? 0;

  const overall_risk_score = Number((0.5 * complaintScore + 0.5 * financialScore).toFixed(2));
  const overall_risk_level = getOverallRiskLevel(overall_risk_score);

  const warnings = [];
  if (overall_risk_level === 'High' || overall_risk_level === 'Critical') {
    warnings.push(`Overall risk is ${overall_risk_level} (score: ${overall_risk_score.toFixed(2)})`);
  }
  if (complaintResult.complaint_risk_level === 'High' || complaintResult.complaint_risk_level === 'Critical') {
    warnings.push(`High complaint risk (${complaintScore.toFixed(2)})`);
  }
  if (financialResult.financial_risk_level === 'High' || financialResult.financial_risk_level === 'Critical') {
    warnings.push(`High financial risk (${financialScore.toFixed(2)})`);
  }

  const early_warning = warnings.length > 0 ? `EARLY WARNING: ${warnings.join('. ')}.` : 'No Early Warning';

  return {
    overall_risk_score,
    overall_risk_level,
    early_warning,
  };
}

module.exports = {
  calculateOverallRisk,
};
// financialRisk.js
// Ported from the AI team's notebook (Financial Risk Analysis section)
// Uses FIXED thresholds, so it works per-company without needing other companies' data.

function safeDivide(a, b) {
  if (b === 0 || b === null || b === undefined || a === null || a === undefined) return null;
  return a / b;
}

function scoreProfitMargin(x) {
  if (x === null) return null;
  if (x >= 0.15) return 0;
  if (x >= 0.1) return 25;
  if (x >= 0.05) return 50;
  if (x >= 0) return 75;
  return 100;
}

function scoreProfitGrowth(x) {
  if (x === null) return null;
  if (x >= 0) return 0;
  if (x >= -0.1) return 25;
  if (x >= -0.25) return 50;
  if (x >= -0.5) return 75;
  return 100;
}

function scoreRevenueGrowth(x) {
  if (x === null) return null;
  if (x >= 0) return 0;
  if (x >= -0.1) return 25;
  if (x >= -0.2) return 50;
  if (x >= -0.4) return 75;
  return 100;
}

function scoreDebtGrowth(x) {
  if (x === null) return null;
  if (x <= 0) return 0;
  if (x <= 0.1) return 25;
  if (x <= 0.25) return 50;
  if (x <= 0.5) return 75;
  return 100;
}

function scoreCurrentRatio(x) {
  if (x === null) return null;
  if (x >= 2) return 0;
  if (x >= 1.5) return 25;
  if (x >= 1) return 50;
  if (x >= 0.75) return 75;
  return 100;
}

function scoreDebtToEquity(x) {
  if (x === null) return null;
  if (x < 0) return 100;
  if (x <= 1) return 0;
  if (x <= 2) return 25;
  if (x <= 3) return 50;
  if (x <= 5) return 75;
  return 100;
}

function scoreCashGrowth(x) {
  if (x === null) return null;
  if (x >= 0) return 0;
  if (x >= -0.1) return 25;
  if (x >= -0.25) return 50;
  if (x >= -0.5) return 75;
  return 100;
}

function scoreEquityGrowth(x) {
  if (x === null) return null;
  if (x >= 0) return 0;
  if (x >= -0.1) return 25;
  if (x >= -0.25) return 50;
  if (x >= -0.5) return 75;
  return 100;
}

function getFinancialRiskLevel(score) {
  if (score === null) return 'Unknown';
  if (score < 40) return 'Low';
  if (score < 60) return 'Medium';
  if (score < 80) return 'High';
  return 'Critical';
}

function pctChange(current, previous) {
  if (previous === null || previous === undefined || previous === 0) return null;
  if (current === null || current === undefined) return null;
  return (current - previous) / previous;
}

// current: latest period row { revenue, net_profit, total_assets, total_liabilities,
//                               total_debt, equity, cash, current_assets, current_liabilities }
// previous: same shape, previous period (for growth calcs). Pass null if not available.
function calculateFinancialRisk(current, previous = null) {
  const profit_margin = safeDivide(current.net_profit, current.revenue);
  const debt_to_equity = safeDivide(current.total_debt, current.equity);
  const current_ratio = safeDivide(current.current_assets, current.current_liabilities);

  const revenue_growth = previous ? pctChange(current.revenue, previous.revenue) : null;
  const profit_growth = previous ? pctChange(current.net_profit, previous.net_profit) : null;
  const debt_growth = previous ? pctChange(current.total_debt, previous.total_debt) : null;
  const cash_growth = previous ? pctChange(current.cash, previous.cash) : null;
  const equity_growth = previous ? pctChange(current.equity, previous.equity) : null;

  const profit_margin_risk = scoreProfitMargin(profit_margin);
  const profit_growth_risk = scoreProfitGrowth(profit_growth);
  const revenue_risk = scoreRevenueGrowth(revenue_growth);
  const debt_growth_risk = scoreDebtGrowth(debt_growth);
  const liquidity_risk = scoreCurrentRatio(current_ratio);
  const leverage_risk = scoreDebtToEquity(debt_to_equity);
  const cash_risk = scoreCashGrowth(cash_growth);
  const equity_risk = scoreEquityGrowth(equity_growth);

  const profitabilityParts = [profit_margin_risk, profit_growth_risk].filter((v) => v !== null);
  const profitability_risk =
    profitabilityParts.length > 0
      ? profitabilityParts.reduce((a, b) => a + b, 0) / profitabilityParts.length
      : null;

  const weights = {
    profitability_risk: 0.25,
    liquidity_risk: 0.2,
    leverage_risk: 0.2,
    debt_growth_risk: 0.15,
    revenue_risk: 0.1,
    cash_risk: 0.05,
    equity_risk: 0.05,
  };

  const components = {
    profitability_risk,
    liquidity_risk,
    leverage_risk,
    debt_growth_risk,
    revenue_risk,
    cash_risk,
    equity_risk,
  };

  let weightedSum = 0;
  let availableWeight = 0;
  for (const [key, value] of Object.entries(components)) {
    if (value !== null && value !== undefined) {
      weightedSum += value * weights[key];
      availableWeight += weights[key];
    }
  }

  const financial_risk_score = availableWeight > 0 ? Number((weightedSum / availableWeight).toFixed(2)) : null;
  const financial_risk_level = getFinancialRiskLevel(financial_risk_score);

  const factorLabels = {
    profitability_risk: 'Profitability',
    liquidity_risk: 'Liquidity',
    leverage_risk: 'Leverage',
    debt_growth_risk: 'Debt Growth',
    revenue_risk: 'Revenue Decline',
    cash_risk: 'Cash Decline',
    equity_risk: 'Equity Decline',
  };

  let main_financial_risk_factor = null;
  let maxVal = -1;
  for (const [key, value] of Object.entries(components)) {
    if (value !== null && value > maxVal) {
      maxVal = value;
      main_financial_risk_factor = factorLabels[key];
    }
  }

  const reasons = [];
  if (profitability_risk >= 60) reasons.push('weak profitability or declining profit');
  if (liquidity_risk >= 60) reasons.push('low liquidity position');
  if (leverage_risk >= 60) reasons.push('high leverage level');
  if (debt_growth_risk >= 60) reasons.push('rapid debt growth');
  if (revenue_risk >= 60) reasons.push('declining revenue');
  if (cash_risk >= 60) reasons.push('declining cash position');
  if (equity_risk >= 60) reasons.push('declining equity');

  const financial_risk_explanation =
    reasons.length === 0
      ? 'No major financial risk drivers detected.'
      : `Main financial risk drivers: ${reasons.join(', ')}.`;

  return {
    financial_risk_score,
    financial_risk_level,
    main_financial_risk_factor,
    financial_risk_explanation,
    profitability_risk,
    liquidity_risk,
    leverage_risk,
    debt_growth_risk,
    revenue_risk,
    cash_risk,
    equity_risk,
  };
}

module.exports = {
  calculateFinancialRisk,
};
// complaintRisk.js
// Ported from the AI team's notebook (Complaints Risk Analysis section)

// Normalize a value to 0-100 scale based on min/max across ALL companies
function normalizeScore(value, min, max) {
  if (max === min) return 0;
  return ((value - min) / (max - min)) * 100;
}

// Step 1: Aggregate raw complaint rows into per-company stats
function aggregateComplaintsByCompany(complaintsRows) {
  const grouped = {};

  for (const row of complaintsRows) {
    const id = row.company_id;
    if (!grouped[id]) {
      grouped[id] = {
        company_id: id,
        complaint_count: 0,
        negative_complaints: 0,
        high_severity: 0,
        open_complaints: 0,
        fraud_complaints: 0,
        monthly: {},
      };
    }

    const g = grouped[id];
    g.complaint_count += 1;
    if (row.sentiment === 'negative') g.negative_complaints += 1;
    if (row.severity === 'high') g.high_severity += 1;
    if (row.status === 'open') g.open_complaints += 1;
    if (row.category === 'fraud') g.fraud_complaints += 1;

    const month = new Date(row.complaint_date).toISOString().slice(0, 7);
    g.monthly[month] = (g.monthly[month] || 0) + 1;
  }

  return Object.values(grouped);
}

// Step 2: Add ratios + latest month-over-month growth
function addRatiosAndGrowth(companyStats) {
  return companyStats.map((c) => {
    const negative_ratio = c.negative_complaints / c.complaint_count;
    const high_severity_ratio = c.high_severity / c.complaint_count;
    const open_ratio = c.open_complaints / c.complaint_count;
    const fraud_ratio = c.fraud_complaints / c.complaint_count;

    const months = Object.keys(c.monthly).sort();
    let complaint_growth = 0;
    if (months.length >= 2) {
      const prev = c.monthly[months[months.length - 2]];
      const last = c.monthly[months[months.length - 1]];
      complaint_growth = prev === 0 ? 0 : (last - prev) / prev;
    }

    return {
      ...c,
      negative_ratio,
      high_severity_ratio,
      open_ratio,
      fraud_ratio,
      complaint_growth,
    };
  });
}

// Step 3: Normalize all indicators across the full company set (min/max),
// then compute weighted complaint_risk_score for every company
function calculateComplaintRiskScores(companyStats) {
  const withRatios = addRatiosAndGrowth(companyStats);

  const volumeVals = withRatios.map((c) => c.complaint_count);
  const negativeVals = withRatios.map((c) => c.negative_ratio);
  const severityVals = withRatios.map((c) => c.high_severity_ratio);
  const openVals = withRatios.map((c) => c.open_ratio);
  const fraudVals = withRatios.map((c) => c.fraud_ratio);
  const growthVals = withRatios.map((c) => Math.max(c.complaint_growth, 0));

  const bounds = (arr) => ({ min: Math.min(...arr), max: Math.max(...arr) });
  const volumeB = bounds(volumeVals);
  const negativeB = bounds(negativeVals);
  const severityB = bounds(severityVals);
  const openB = bounds(openVals);
  const fraudB = bounds(fraudVals);
  const growthB = bounds(growthVals);

  return withRatios.map((c) => {
    const volume_score = normalizeScore(c.complaint_count, volumeB.min, volumeB.max);
    const negative_score = normalizeScore(c.negative_ratio, negativeB.min, negativeB.max);
    const severity_score = normalizeScore(c.high_severity_ratio, severityB.min, severityB.max);
    const open_score = normalizeScore(c.open_ratio, openB.min, openB.max);
    const fraud_score = normalizeScore(c.fraud_ratio, fraudB.min, fraudB.max);
    const growth_score = normalizeScore(Math.max(c.complaint_growth, 0), growthB.min, growthB.max);

    const complaint_risk_score = Number(
      (
        0.2 * volume_score +
        0.2 * negative_score +
        0.2 * severity_score +
        0.15 * open_score +
        0.1 * fraud_score +
        0.15 * growth_score
      ).toFixed(2)
    );

    const complaint_risk_level = getComplaintRiskLevel(complaint_risk_score);

    const contributions = {
      'High complaint volume': volume_score * 0.2,
      'High negative sentiment': negative_score * 0.2,
      'High severity complaints': severity_score * 0.2,
      'High number of open complaints': open_score * 0.15,
      'Fraud-related complaints': fraud_score * 0.1,
      'Increasing complaint activity': growth_score * 0.15,
    };

    const risk_drivers = Object.entries(contributions)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([label]) => label);

    const complaint_early_warning =
      complaint_risk_level === 'High' || complaint_risk_level === 'Critical'
        ? `Early Warning: ${complaint_risk_level} complaint risk. Main drivers: ${risk_drivers.join(', ')}.`
        : 'No high-risk complaint warning.';

    return {
      company_id: c.company_id,
      complaint_risk_score,
      complaint_risk_level,
      risk_drivers,
      complaint_early_warning,
    };
  });
}

function getComplaintRiskLevel(score) {
  if (score >= 85) return 'Critical';
  if (score >= 70) return 'High';
  if (score >= 40) return 'Medium';
  return 'Low';
}

module.exports = {
  aggregateComplaintsByCompany,
  calculateComplaintRiskScores,
};
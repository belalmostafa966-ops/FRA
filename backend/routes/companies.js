// backend/routes/companies.js
const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/companies — list all companies (for the dashboard table/cards)
router.get('/', async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT id, name, license_number, sector, status,
              complaint_risk, financial_risk, overall_risk,
              risk_level, last_scored_at, created_at
       FROM companies
       ORDER BY overall_risk DESC`
    );
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: 'Failed to fetch companies' });
  }
});

// GET /api/companies/:id — single company profile page
// Returns company info + its recent complaints + its recent financial records
router.get('/:id', async (req, res) => {
  const { id } = req.params;

  try {
    const [companyRows] = await db.query(
      `SELECT * FROM companies WHERE id = ?`,
      [id]
    );

    if (companyRows.length === 0) {
      return res.status(404).json({ success: false, error: 'Company not found' });
    }

    const [complaints] = await db.query(
      `SELECT id, complaint_date, category, sentiment, severity, status, source
       FROM complaints
       WHERE company_id = ?
       ORDER BY complaint_date DESC
       LIMIT 20`,
      [id]
    );

    const [financialData] = await db.query(
      `SELECT id, period, revenue, net_profit, total_assets, total_liabilities,
              total_debt, equity, cash, current_assets, current_liabilities
       FROM financial_data
       WHERE company_id = ?
       ORDER BY period DESC
       LIMIT 8`,
      [id]
    );

    res.json({
      company: companyRows[0],
      complaints,
      financial_data: financialData,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: 'Failed to fetch company details' });
  }
});

module.exports = router;
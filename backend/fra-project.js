require('dotenv').config();
const express = require('express');
const cors = require('cors');
const db = require('./db');

// 1. استدعاء الـ Routes والـ Middlewares في البداية
const { requireAuth } = require('./middleware/middleware_auth');
const authRouter = require('./routes/auth');
const companiesRouter = require('./routes/companies');

const { aggregateComplaintsByCompany, calculateComplaintRiskScores } = require('./riskEngine/complaintRisk');
const { calculateFinancialRisk } = require('./riskEngine/financialRisk');
const { calculateOverallRisk } = require('./riskEngine/overallRisk');

const app = express();
const PORT = process.env.PORT || 5050;

// 2. الـ Middlewares العامة
app.use(cors());
app.use(express.json());

// 3. ربط الـ Routes بعد تعريفها
app.use('/api/auth', authRouter);
app.use('/api/companies', requireAuth, companiesRouter);

// راوت تجريبي - للتأكد إن السيرفر شغال
app.get('/', (req, res) => {
  res.json({ message: 'Backend is running successfully!' });
});

// راوت تجريبي - للتأكد إن الاتصال بالداتابيز شغال
app.get('/test-db', async (req, res) => {
  try {
    const [rows] = await db.query('SELECT 1 + 1 AS result');
    res.json({ success: true, result: rows[0].result });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ================== Risk Analysis Route ==================
app.get('/api/risk/:companyId', async (req, res) => {
  try {
    const companyId = Number(req.params.companyId);

    // 1. Complaint risk needs ALL companies' complaints (for min/max normalization)
    const [allComplaints] = await db.query(
      'SELECT company_id, sentiment, severity, status, category, complaint_date FROM complaints'
    );

    const companyStats = aggregateComplaintsByCompany(allComplaints);
    const allComplaintScores = calculateComplaintRiskScores(companyStats);
    const complaintResult = allComplaintScores.find((c) => c.company_id === companyId);

    if (!complaintResult) {
      return res.status(404).json({ error: 'No complaint data found for this company' });
    }

    // 2. Financial risk only needs THIS company's latest + previous period
    const [financialRows] = await db.query(
      'SELECT * FROM financial_data WHERE company_id = ? ORDER BY period DESC LIMIT 2',
      [companyId]
    );

    if (financialRows.length === 0) {
      return res.status(404).json({ error: 'No financial data found for this company' });
    }

    const current = financialRows[0];
    const previous = financialRows.length > 1 ? financialRows[1] : null;
    const financialResult = calculateFinancialRisk(current, previous);

    // 3. Combine
    const overallResult = calculateOverallRisk(complaintResult, financialResult);

    res.json({
      company_id: companyId,
      ...complaintResult,
      ...financialResult,
      ...overallResult,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Risk analysis failed', details: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
});
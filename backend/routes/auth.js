// backend/routes/auth.js
const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../db');

const JWT_SECRET = process.env.JWT_SECRET || 'change_this_secret_in_env_file';

// POST /api/auth/register — create a new FRA user (admin/analyst/supervisor)
router.post('/register', async (req, res) => {
  const { name, email, password, role } = req.body;

  if (!name || !email || !password) {
    return res.status(400).json({ success: false, error: 'name, email and password are required' });
  }

  try {
    // check if email already exists
    const [existing] = await db.query('SELECT id FROM fra_users WHERE email = ?', [email]);
    if (existing.length > 0) {
      return res.status(409).json({ success: false, error: 'Email already registered' });
    }

    const password_hash = await bcrypt.hash(password, 10);

    const [result] = await db.query(
      `INSERT INTO fra_users (name, email, password_hash, role) VALUES (?, ?, ?, ?)`,
      [name, email, password_hash, role || 'analyst']
    );

    res.status(201).json({ success: true, user_id: result.insertId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: 'Registration failed' });
  }
});

// POST /api/auth/login — verify credentials and issue a JWT
router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ success: false, error: 'email and password are required' });
  }

  try {
    const [rows] = await db.query('SELECT * FROM fra_users WHERE email = ?', [email]);
    if (rows.length === 0) {
      return res.status(401).json({ success: false, error: 'Invalid email or password' });
    }

    const user = rows[0];
    const passwordMatches = await bcrypt.compare(password, user.password_hash);

    if (!passwordMatches) {
      return res.status(401).json({ success: false, error: 'Invalid email or password' });
    }

    const token = jwt.sign(
      { id: user.id, name: user.name, role: user.role },
      JWT_SECRET,
      { expiresIn: '8h' }
    );

    res.json({
      success: true,
      token,
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: 'Login failed' });
  }
});

module.exports = router;
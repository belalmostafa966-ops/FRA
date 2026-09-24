# FRA Risk Intelligence Platform

> **Enterprise Risk Intelligence & Supervisory Platform** for the Financial Regulatory Authority (FRA) to monitor, evaluate, and inspect Non-Banking Financial Institutions (NBFIs).

---

## Overview

The **FRA Risk Intelligence Platform** is a production-grade supervisory web dashboard engineered for regulatory bodies and financial analysts. It automates financial risk scoring, early warning alert detection (EWS), risk-based field inspection scheduling, and regulatory task force management across non-banking financial sectors (Microfinance, Consumer Finance, Insurance, Capital Markets, Leasing).

Built with **Python**, **Streamlit**, **SQLAlchemy**, and **Plotly**, the application features a clean, high-density SaaS Admin interface with Western English digits (`0-9`), robust JWT authentication with strict session isolation, role-based access control (RBAC), SMTP automated email dispatch, and modal report downloads.

---

## Key Features & Recent Enhancements

### 1. 🔑 Fresh Session Isolation per Login
- **Isolated User Sessions**: On every login (manual form or quick demo button), previous session states and URL query parameters are purged (`st.session_state.clear()`).
- **Unique JWT & Session Nonce**: Each login generates a fresh JWT token with a unique UUID `session_nonce` preventing cross-user state leakage or tab ghosting.

### 2. 🕵️ Role-Based Inspection Workflow & Inspector Access Level
- **Inspector Role (`inspector` / `Inspector@123`)**: Dedicated UI tab view exclusively showing assigned field inspection tasks (`assigned_to_user_id == user.id`).
- **Audit Findings & Evidence Upload**: Inspectors can log detailed violation notes, update task lifecycle status (`Scheduled`, `In Progress`, `Completed`, `Cancelled`), adjust evaluated entity risk levels, and upload audit evidence files (`.pdf`, `.docx`, `.xlsx`, `.png`, `.jpg`).
- **Manager Supervisory Review**: Admins & Risk Analysts review inspector submissions, add supervisory comments, approve/reject findings, and download attached evidence files.
- **Automated SMTP Email Alerts**: Automatically sends email notifications to assigned inspectors upon task dispatch and to managers upon field findings submission.

### 3. 📄 Report & Evidence File Downloads
- **Statutory Audit Downloads**: Download attached regulatory reports and evidence files directly from entity modal popups, company deep-dives, and inspection review tabs.
- **Text & Binary Support**: Dynamic file handling with `st.download_button` for audit documents.

### 4. 🗑️ Entity & Account Management (Admin & Analyst)
- **Full Entity Deletion**: Dedicated "Delete Monitored Entity" subtab with cascade database cleanup (`delete_company_entity`) purging associated complaints, financials, risk histories, inspection tasks, and reports.
- **User Account Deletion & Role Modification**: Admins can manage existing user accounts, modify assigned roles, toggle active status, or permanently delete user accounts.

### 5. 🔢 Western English Digits & Visual Design
- **Strict Western Numerals (`0-9`)**: Global CSS typography rules (`font-variant-numeric: lining-nums tabular-nums !important; font-feature-settings: 'lnum' 1, 'tnum' 1 !important; direction: ltr !important;`) forcing Western numbers across all inputs, metrics, tables, and dialogs.
- **Official FRA Branding**: Navy Blue (`#0F172A`), Regal Gold (`#D97706`), and Slate styling with zero-emojis.

---

## 🛠️ Technology Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/) with Custom Enterprise CSS Design System
- **Programming Language**: Python 3.10+
- **Database & ORM**: SQLAlchemy (Supports **MySQL / MariaDB** via XAMPP with fallback to **SQLite**)
- **Data Analytics & Visualization**: Pandas, NumPy, Plotly
- **Security & Auth**: PyJWT, Passlib (bcrypt hashing), Bleach (HTML input sanitization)
- **Email Communications**: Python `smtplib` (SMTP automated notifications)

---

## 🚀 Getting Started & Installation

### Prerequisites
- Python 3.10 or higher
- Git
- (Optional) XAMPP / MySQL Server

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/fra-risk-platform.git
cd fra-risk-platform
```

### 2. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database & Seed Default Records
Run the automated database setup script:
```bash
python setup_db.py
```

### 5. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser and navigate to: **`http://localhost:8501`**

---

## 🔑 Default Credentials for Demo Testing

| Username | Email | Password | Role | System Access Level |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | `admin@fra.gov.eg` | `Admin@123` | **Admin** | Full access to all modules, Admin Control Panel, User Account Management, Entity Deletion |
| `analyst` | `analyst@fra.gov.eg` | `Analyst@123` | **Risk Analyst** | Risk Engine, Inspection Task Dispatch & Manager Review, Analyst Hub, Entity Edit/Delete |
| `executive` | `executive@fra.gov.eg` | `Exec@123` | **Executive** | Executive Oversight Dashboard & Company Deep-Dive |
| `inspector` | `inspector@fra.gov.eg` | `Inspector@123` | **Inspector** | Dedicated Inspection Task View, Findings Logging, Evidence File Upload |

---

## 📁 Repository Structure

```
fra-risk-platform/
├── app.py                      # Main application entry point & RBAC router
├── auth.py                     # JWT token encoding/decoding & bcrypt hashing
├── config.py                   # Environment & Database URL configuration
├── database.py                 # SQLAlchemy engine & session factory
├── models.py                   # Database schema definitions (ORM models)
├── setup_db.py                 # Automated SQL database creation & seeding script
├── custom_theme.py             # Enterprise SaaS light/dark CSS design system
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── risk_engine/                # Risk calculation algorithms & scoring rules
│   ├── financial.py
│   └── complaints.py
├── utils/                      # Helper utilities
│   ├── security.py             # Input sanitization & activity audit logs
│   ├── notifications.py        # Real-Time Notification Center helper
│   ├── company_manager.py      # Company management & cascade deletion helpers
│   ├── company_modal.py        # Comprehensive popup dialog modal
│   └── data_seeder.py          # Sample dataset generator
└── views/                      # Dashboard UI views
    ├── login.py                # Supervisory access login view with session isolation
    ├── executive_dashboard.py  # Executive overview & KPIs
    ├── company_deepdive.py     # Entity risk deep-dive & report generator
    ├── analyst_hub.py          # Risk Analyst hub & weight adjustments
    ├── inspection_scheduler.py # Risk-Based Inspection Scheduler & Task Force Manager
    └── admin_panel.py          # Admin control panel, user management & audit logs
```

---

## 📄 License
This project is created for educational and regulatory supervisory demonstration purposes.


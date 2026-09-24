# 🏛️ FRA Risk Intelligence Platform

> **Enterprise Risk Intelligence & Supervisory Platform** designed for the **Financial Regulatory Authority (FRA)** to monitor, evaluate, and inspect Non-Banking Financial Institutions (NBFIs) in Egypt (Microfinance, Consumer Finance, Insurance, Capital Markets, Leasing, Real Estate Finance).

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Hierarchical Roles & Operational Workflows](#hierarchical-roles--operational-workflows)
   - [1. System Administrator (`admin`)](#1-system-administrator-admin)
   - [2. Risk Analyst (`analyst`)](#2-risk-analyst-analyst)
   - [3. Executive Leadership (`executive`)](#3-executive-leadership-executive)
   - [4. Field Inspector (`inspector`)](#4-field-inspector-inspector)
3. [Deep-Dive Feature Breakdown](#deep-dive-feature-breakdown)
   - [A. Early Warning System (EWS) & Risk Engine](#a-early-warning-system-ews--risk-engine)
   - [B. Comprehensive Company Deep-Dive Analytics](#b-comprehensive-company-deep-dive-analytics)
   - [C. Inspection Lifecycle & Evidence File Upload](#c-inspection-lifecycle--evidence-file-upload)
   - [D. Session Isolation & Security Governance](#d-session-isolation--security-governance)
   - [E. Automated SMTP Email Notification Center](#e-automated-smtp-email-notification-center)
4. [Technology Stack](#technology-stack)
5. [Repository Structure](#repository-structure)
6. [Getting Started & Installation](#getting-started--installation)
7. [Default Credentials](#default-credentials)
8. [License & Support](#license--support)

---

## Overview

The **FRA Risk Intelligence Platform** is a production-grade supervisory web dashboard engineered for financial regulators, auditors, and leadership. It automates financial risk scoring, early warning alert detection (EWS), risk-based field inspection scheduling, and task force management across non-banking financial sectors.

Built with **Python**, **Streamlit**, **SQLAlchemy**, and **Plotly**, the application features a high-density SaaS interface formatted with strict Western English digits (`0-9`), robust JWT authentication with session isolation, role-based access control (RBAC), SMTP automated email dispatch, and audit file management.

---

## Hierarchical Roles & Operational Workflows

The platform is structured around a strict hierarchy from highest authority to field execution. Each role has a specialized portal tailored to its daily operations.

```
       ┌────────────────────────────────────────────────────────┐
       │         1. System Administrator (admin)                │
       │  • User Lifecycle & RBAC • Cascade Entity Cleanup      │
       │  • SMTP Configuration    • System Security Logs        │
       └───────────────────────────┬────────────────────────────┘
                                   │
       ┌───────────────────────────▼────────────────────────────┐
       │           2. Risk Analyst (analyst)                    │
       │  • Dynamic Risk Weight Tuning • Inspection Dispatch    │
       │  • Supervisory Review & Approval • Deep Analytics      │
       └───────────────────────────┬────────────────────────────┘
                                   │
       ┌───────────────────────────▼────────────────────────────┐
       │         3. Executive Leadership (executive)            │
       │  • High-Level KPIs & Macro Sector Oversight            │
       │  • Live EWS Alerts Feed & Board Reports                │
       └───────────────────────────┬────────────────────────────┘
                                   │
       ┌───────────────────────────▼────────────────────────────┐
       │          4. Field Inspector (inspector)                │
       │  • Dedicated Field Task Portal • Log Findings          │
       │  • Direct Risk Adjustment  • Evidence Document Upload  │
       └────────────────────────────────────────────────────────┘
```

---

### 1. System Administrator (`admin`)
*Highest Level of System Authority & Governance*

- **User Lifecycle & Role Assignment**: Create new user accounts, modify existing user roles (`admin`, `analyst`, `executive`, `inspector`), reset passwords, and activate/deactivate staff accounts.
- **Cascade Entity Deletion**: Safely purge monitored companies from the database with automatic cascading deletion of financial history, complaint logs, risk scores, inspection tasks, and uploaded report files.
- **Inline Data Editing & Data Overrides**: Directly edit audited company parameters (Revenue, Assets, Net Income, CAR, NPL, Complaint volume) in real-time with required audit trail justification notes.
- **SMTP Server Configuration**: Configure custom SMTP mail servers (Host, Port, SSL/TLS, Credentials) for system-wide automated email dispatch.
- **Security Audit Logs**: Inspect system-wide activity logs (`ActivityLog`), tracking exact user actions, modified entity IDs, IP addresses, and timestamps.

---

### 2. Risk Analyst (`analyst`)
*Core Analytical Engine & Inspection Manager*

- **Dynamic Risk Weight Tuning**: Customize the weighted scoring model ($w_f$ Financial, $w_c$ Complaints, $w_v$ Violations) for composite risk score calculations across all sectors.
- **Inspection Task Force Dispatch**: Schedule risk-based field inspections, assign target companies to specific field inspectors, define inspection scope, set target deadlines, and trigger automatic email alerts to inspectors.
- **Supervisory Manager Review**: Review findings submitted by field inspectors, read audit notes, inspect uploaded evidence files (`.pdf`, `.docx`, `.xlsx`, `.png`), add manager review comments, and formally **Approve** or **Reject** inspection reports.
- **Company Deep-Dive Analytics**: Access full financial histories, historical complaint sentiment breakdowns, sector benchmarking, and download attached statutory reports.

---

### 3. Executive Leadership (`executive`)
*Strategic Macro Oversight & Decision Support*

- **Executive KPI Dashboard**: Instant visibility over macroeconomic financial metrics, total monitored portfolio assets, sector-wide risk distributions, and unresolved high-severity complaints.
- **Live Early Warning System (EWS) Feed**: Monitor real-time alert tickers highlighting companies breaching risk thresholds or showing sharp degradation in financial ratios.
- **Strategic Sector Comparison**: High-level visual heatmaps comparing risk concentrations across Microfinance, Consumer Finance, Insurance, Capital Markets, and Leasing.

---

### 4. Field Inspector (`inspector`)
*Field Execution & Audit Findings Logging*

- **Dedicated Inspector Portal**: A streamlined view displaying **only** tasks assigned directly to the logged-in inspector (`assigned_to_user_id == user.id`).
- **Task Lifecycle Management**: Transition inspection tasks through lifecycle statuses (`Scheduled` ➔ `In Progress` ➔ `Completed` ➔ `Cancelled`).
- **Audit Findings Logging**: Input field notes, document regulatory non-compliance, and directly adjust assessed company risk levels based on physical audit evidence.
- **Evidence File Upload**: Attach official field evidence documents (`.pdf`, `.docx`, `.xlsx`, `.png`, `.jpg`) directly to the inspection record for manager review.
- **Automated Alerts**: Receive instant email notifications upon new task assignments and send automatic submission alerts back to supervisory managers upon completing audits.

---

## Deep-Dive Feature Breakdown

### A. Early Warning System (EWS) & Risk Engine
The risk engine evaluates financial institutions using a weighted composite scoring formula (0 – 100):

$$\text{Composite Risk Score} = (w_f \times \text{Financial Risk}) + (w_c \times \text{Complaints Risk}) + (w_v \times \text{Violations Risk})$$

- **Assessed Ratios**: Capital Adequacy Ratio (CAR), Non-Performing Loans (NPL), Return on Assets (ROA), Liquidity Ratio.
- **Risk Tiers**:
  - 🟢 **Low Risk (0 - 33)**: Normal supervisory monitoring.
  - 🟡 **Medium Risk (34 - 66)**: Increased off-site monitoring.
  - 🔴 **High Risk (67 - 100)**: Triggers priority EWS alerts and mandatory field inspection dispatch.

### B. Comprehensive Company Deep-Dive Analytics
- Interactive dialog popups and dedicated deep-dive views.
- Sector comparison benchmarks, financial performance charts, complaint sentiment breakdowns, and direct PDF/Doc report downloads.

### C. Inspection Lifecycle & Evidence File Upload
- End-to-end task force tracking from scheduling to manager approval.
- Support for multi-format evidence file uploads stored safely in dedicated system directories.

### D. Session Isolation & Security Governance
- **Session Cleanup (`st.session_state.clear()`)**: Clears session data upon every login to guarantee zero cross-user state leakage or tab ghosting.
- **JWT Authentication & Nonce**: Employs bcrypt password hashing and PyJWT tokens signed with a unique `session_nonce`.
- **HTML Sanitization**: Uses `bleach` sanitization across all user text inputs to prevent XSS attacks.

### E. Automated SMTP Email Notification Center
- Background email alerts using Python `smtplib`.
- Dispatches task assignment notifications to inspectors and completion reports to managers.

---

## Technology Stack

| Component | Technology Used |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Frontend Framework** | [Streamlit](https://streamlit.io/) with Custom SaaS CSS |
| **Database & ORM** | SQLAlchemy (MySQL / MariaDB via XAMPP with fallback to SQLite) |
| **Analytics & Plotting** | Pandas, NumPy, Plotly Express & Graph Objects |
| **Security & Auth** | PyJWT, Passlib (Bcrypt hashing), Bleach (HTML sanitization) |
| **Email Dispatch** | Python `smtplib` / `email.mime` |

---

## Repository Structure

```
fra/
├── app.py                      # Main entry point & RBAC view router
├── auth.py                     # JWT token encoding/decoding & bcrypt password hashing
├── config.py                   # System configurations & database URLs
├── database.py                 # SQLAlchemy engine & session factory
├── models.py                   # Database schema definitions (User, Company, Complaint, Task, etc.)
├── setup_db.py                 # DB initialization & seeding script
├── custom_theme.py             # SaaS light/dark CSS design system
├── requirements.txt            # Python dependencies
├── README.md                   # Full project documentation
│
├── risk_engine/                # Risk scoring algorithms
│   ├── financial.py            # Financial ratio scoring
│   └── complaints.py           # Complaint severity scoring
│
├── utils/                      # Helper utilities
│   ├── security.py             # Input sanitization & audit log recording
│   ├── notifications.py        # Notification center helper
│   ├── company_manager.py      # Entity management & cascade deletion handler
│   ├── company_modal.py        # Comprehensive popup dialog modal
│   ├── email_service.py        # SMTP email dispatch engine
│   └── data_seeder.py          # Synthetic dataset generator
│
└── views/                      # Dashboard UI Views
    ├── login.py                # Supervisory access login with session isolation
    ├── executive_dashboard.py  # Executive oversight & KPI dashboard
    ├── company_deepdive.py     # Entity risk deep-dive analytics
    ├── analyst_hub.py          # Risk Analyst hub & weight adjustments
    ├── inspection_scheduler.py # Risk-based inspection scheduler & inspector portal
    └── admin_panel.py          # Admin control panel, user RBAC & audit logs
```

---

## Getting Started & Installation

### Prerequisites
- **Python 3.10** or higher
- Git
- (Optional) XAMPP / MySQL Server

### Step-by-Step Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/belalmostafa966-ops/fra-risk-platform.git
   cd fra-risk-platform
   ```

2. **Create & Activate Virtual Environment:**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database & Seed Records:**
   ```bash
   python setup_db.py
   ```

5. **Launch the Web Application:**
   ```bash
   streamlit run app.py
   ```
   Open your browser and navigate to: **`http://localhost:8501`**

---

## Default Credentials

Use these pre-configured accounts to test each role's workflow:

| Username | Email | Password | Role | System Hierarchy Level |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | `admin@fra.gov.eg` | `Admin@123` | **Admin** | 1. Full Governance, User RBAC, Cascade Deletion, Audit Logs |
| `analyst` | `analyst@fra.gov.eg` | `Analyst@123` | **Risk Analyst** | 2. Weight Tuning, Inspection Dispatch, Supervisory Review |
| `executive` | `executive@fra.gov.eg` | `Exec@123` | **Executive** | 3. Macro Dashboard, EWS Alerts, Strategic Analytics |
| `inspector` | `inspector@fra.gov.eg` | `Inspector@123` | **Inspector** | 4. Field Task Portal, Log Findings, Evidence Upload |

---

## License & Support

This platform is developed for supervisory and educational demonstration for the **Financial Regulatory Authority (FRA)**.  
All Rights Reserved © 2026.

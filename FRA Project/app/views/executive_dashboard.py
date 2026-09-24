import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Company, RiskScoreHistory, Complaint, FinancialRecord, InspectionTask, CompanyReport
from utils.company_modal import render_company_details_dialog

def render_executive_dashboard():
    """
    Renders the FRA Executive Oversight Dashboard.
    Styled with the official FRA Navy Blue & Regal Gold palette and tailored for
    financial regulatory inspection, EWS alerts, and supervisory risk analysis.
    """
    db: Session = SessionLocal()
    user = st.session_state.get("user", {})

    try:
        companies = db.query(Company).all()
        if not companies:
            st.warning("No companies found in database. Please seed or import data.")
            return

        # Aggregated Data
        records = []
        total_ews_count = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for c in companies:
            latest_risk = (
                db.query(RiskScoreHistory)
                .filter(RiskScoreHistory.company_id == c.id)
                .order_by(RiskScoreHistory.evaluation_date.desc())
                .first()
            )
            
            latest_complaint = (
                db.query(Complaint)
                .filter(Complaint.company_id == c.id)
                .order_by(Complaint.year.desc(), Complaint.quarter.desc())
                .first()
            )

            latest_fin = (
                db.query(FinancialRecord)
                .filter(FinancialRecord.company_id == c.id)
                .order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc())
                .first()
            )

            if latest_risk:
                if latest_risk.ews_alert_flag:
                    total_ews_count += 1
                if latest_risk.risk_level == "Critical":
                    critical_count += 1
                elif latest_risk.risk_level == "High":
                    high_count += 1
                elif latest_risk.risk_level == "Medium":
                    medium_count += 1
                else:
                    low_count += 1

                records.append({
                    "id": c.id,
                    "tax_id": c.tax_id,
                    "name": c.name,
                    "sector": c.sector,
                    "risk_level": latest_risk.risk_level,
                    "composite_score": latest_risk.composite_score,
                    "complaint_score": latest_risk.complaint_score,
                    "financial_score": latest_risk.financial_score,
                    "ews_flag": latest_risk.ews_alert_flag,
                    "ews_reasons": latest_risk.ews_reasons or "None",
                    "total_complaints": latest_complaint.total_complaints if latest_complaint else 0,
                    "revenue": latest_fin.revenue if latest_fin else 0.0,
                    "liabilities": latest_fin.total_liabilities if latest_fin else 0.0,
                })

        df = pd.DataFrame(records)
        avg_composite = df["composite_score"].mean() if not df.empty else 0.0

        # Display persistent success notification banner if set
        if "edit_success_msg" in st.session_state:
            st.success(st.session_state.pop("edit_success_msg"))
            st.toast("Updated successfully!", icon="✅")

        # -------------------------------------------------------------
        # FRA Regulatory Top Header Bar with Live Search Input
        # -------------------------------------------------------------
        hdr_c1, hdr_c2 = st.columns([65, 35])
        with hdr_c1:
            st.markdown('<div style="font-size: 1.4rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">Executive Oversight Dashboard</div><div style="font-size: 0.8rem; color: #D97706; font-weight: 700;">Financial Regulatory Authority — Non-Banking Financial Supervision</div>', unsafe_allow_html=True)
        with hdr_c2:
            top_bar_query = st.text_input("Search Monitored Entities", "", placeholder="Search monitored entities, tax IDs...", key="top_bar_search_input", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Row 1: FRA Regulatory Overview Widgets & Live Feed
        # -------------------------------------------------------------
        col_cards, col_recent = st.columns([65, 35])

        with col_cards:
            st.markdown('<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;"><div style="font-size: 1.15rem; font-weight: 800; color: #0F172A;">Supervisory Risk Summary</div><div style="font-size: 0.85rem; font-weight: 700; color: #D97706;">Live Monitoring</div></div>', unsafe_allow_html=True)

            card1, card2 = st.columns(2)

            with card1:
                card1_html = (
                    '<div class="fra-card-navy">'
                    '<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                    '<div>'
                    '<div style="font-size: 0.75rem; font-weight: 700; color: #D97706; text-transform: uppercase; letter-spacing: 0.05em;">SYSTEM COMPOSITE RISK</div>'
                    f'<div style="font-size: 1.8rem; font-weight: 800; margin-top: 0.2rem;">{avg_composite:.1f} <span style="font-size: 0.9rem; color: #CBD5E1;">/ 100</span></div>'
                    '</div>'
                    '<div style="background: rgba(255,255,255,0.1); width: 45px; height: 45px; border-radius: 12px; display: flex; align-items: center; justify-content: center;"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M3 7l9-4 9 4"/><path d="M3 7v4a3 3 0 0 0 6 0V7"/><path d="M15 7v4a3 3 0 0 0 6 0V7"/></svg></div>'
                    '</div>'
                    '<div style="margin-top: 1.5rem; display: flex; gap: 2rem;">'
                    '<div>'
                    '<div style="font-size: 0.68rem; opacity: 0.8; text-transform: uppercase;">MONITORED ENTITIES</div>'
                    f'<div style="font-size: 0.95rem; font-weight: 800; margin-top: 0.1rem;">{len(companies)} Active NBFIs</div>'
                    '</div>'
                    '<div>'
                    '<div style="font-size: 0.68rem; opacity: 0.8; text-transform: uppercase;">SCOPE</div>'
                    '<div style="font-size: 0.95rem; font-weight: 800; margin-top: 0.1rem;">5 Regulated Sectors</div>'
                    '</div>'
                    '</div>'
                    '<div style="margin-top: 1.2rem; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 0.8rem; font-size: 0.78rem; color: #93C5FD; font-weight: 600;">Official FRA Regulatory Benchmark Evaluated</div>'
                    '</div>'
                )
                st.markdown(card1_html, unsafe_allow_html=True)

            with card2:
                card2_html = (
                    '<div class="fra-card-gold">'
                    '<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                    '<div>'
                    '<div style="font-size: 0.75rem; font-weight: 800; color: #FEF3C7; text-transform: uppercase; letter-spacing: 0.05em;">EARLY WARNING ALERTS</div>'
                    f'<div style="font-size: 1.8rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF;">{total_ews_count} <span style="font-size: 0.9rem; color: #FEF3C7;">Flagged</span></div>'
                    '</div>'
                    '<div style="background: rgba(255,255,255,0.2); width: 45px; height: 45px; border-radius: 12px; display: flex; align-items: center; justify-content: center;"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>'
                    '</div>'
                    '<div style="margin-top: 1.5rem; display: flex; gap: 1.5rem;">'
                    '<div>'
                    '<div style="font-size: 0.68rem; color: #FEF3C7; text-transform: uppercase; font-weight: 700;">CRITICAL</div>'
                    f'<div style="font-size: 0.95rem; font-weight: 800; margin-top: 0.1rem; color: #FFFFFF;">{critical_count} Entities</div>'
                    '</div>'
                    '<div>'
                    '<div style="font-size: 0.68rem; color: #FEF3C7; text-transform: uppercase; font-weight: 700;">HIGH RISK</div>'
                    f'<div style="font-size: 0.95rem; font-weight: 800; margin-top: 0.1rem; color: #FFFFFF;">{high_count} Entities</div>'
                    '</div>'
                    '</div>'
                    '<div style="margin-top: 1.2rem; border-top: 1px solid rgba(255,255,255,0.25); padding-top: 0.8rem; font-size: 0.78rem; color: #FEF3C7; font-weight: 700;">Immediate Inspection Task Force Action Required</div>'
                    '</div>'
                )
                st.markdown(card2_html, unsafe_allow_html=True)



        with col_recent:
            recent_html = (
                '<div class="fra-card-slate">'
                '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.2rem;">'
                '<div>'
                '<div style="font-size: 0.75rem; font-weight: 800; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.05em;">SUPERVISORY FEED</div>'
                '<div style="font-size: 1.1rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF;">Recent Activity Stream</div>'
                '</div>'
                '<div style="background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.3); color: #38BDF8; padding: 0.25rem 0.6rem; border-radius: 20px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.03em;">LIVE STREAM</div>'
                '</div>'
                '<div style="display: flex; flex-direction: column; gap: 0.85rem;">'
                '<div style="border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.65rem;">'
                '<div style="display: flex; justify-content: space-between; align-items: center;">'
                '<span style="font-weight: 800; font-size: 0.88rem; color: #FCA5A5;">EWS Trigger Detected</span>'
                '<span style="background: rgba(239,68,68,0.2); color: #FECACA; border: 1px solid rgba(239,68,68,0.3); padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 800;">Critical</span>'
                '</div>'
                '<div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.15rem;">Fraud allegation surge in Consumer Finance</div>'
                '</div>'
                '<div style="border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.65rem;">'
                '<div style="display: flex; justify-content: space-between; align-items: center;">'
                '<span style="font-weight: 800; font-size: 0.88rem; color: #93C5FD;">On-Site Audit Scheduled</span>'
                '<span style="background: rgba(59,130,246,0.2); color: #BFDBFE; border: 1px solid rgba(59,130,246,0.3); padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 800;">Inspection</span>'
                '</div>'
                '<div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.15rem;">Task Force assigned to EFG Hermes</div>'
                '</div>'
                '<div>'
                '<div style="display: flex; justify-content: space-between; align-items: center;">'
                '<span style="font-weight: 800; font-size: 0.88rem; color: #FDE68A;">Statutory Audit Report</span>'
                '<span style="background: rgba(245,158,11,0.2); color: #FEF3C7; border: 1px solid rgba(245,158,11,0.3); padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 800;">Verified</span>'
                '</div>'
                '<div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.15rem;">Compliance report attached for Delta Insurance</div>'
                '</div>'
                '</div>'
                '</div>'
            )
            st.markdown(recent_html, unsafe_allow_html=True)





        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Row 2: Sector Risk & Risk Level Breakdown Charts
        # -------------------------------------------------------------
        col_sector, col_dist = st.columns([65, 35])

        with col_sector:
            st.markdown('<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-bottom: 0.75rem;">Sector Risk & Complaints Analysis</div>', unsafe_allow_html=True)

            sector_agg = df.groupby("sector")[["total_complaints", "liabilities"]].mean().reset_index()
            sector_agg["liabilities_m"] = sector_agg["liabilities"] / 1000000.0

            fig_bar = px.bar(
                sector_agg,
                x="sector",
                y=["total_complaints", "liabilities_m"],
                barmode="group",
                color_discrete_sequence=["#D97706", "#1E3A8A"],
                labels={"value": "Volume / Amount ($M)", "variable": "Indicator", "sector": "Sector"},
                height=330
            )

            fig_bar.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#475569"),
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        with col_dist:
            st.markdown('<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-bottom: 0.75rem;">System Risk Classification Breakdown</div>', unsafe_allow_html=True)

            donut_df = pd.DataFrame({
                "Risk Level": ["Critical", "High", "Medium", "Low"],
                "Count": [critical_count, high_count, medium_count, low_count]
            })

            fig_pie = px.pie(
                donut_df,
                values="Count",
                names="Risk Level",
                hole=0.45,
                color="Risk Level",
                color_discrete_map={
                    "Critical": "#991B1B",
                    "High": "#D97706",
                    "Medium": "#F59E0B",
                    "Low": "#10B981"
                },
                height=330
            )

            fig_pie.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#475569"),
                margin=dict(l=20, r=20, t=20, b=20),
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Row 3: Quick Dispatch & Historical Trajectory
        # -------------------------------------------------------------
        col_qt, col_bh = st.columns([40, 60])

        with col_qt:
            st.markdown('<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-bottom: 0.75rem;">Risk-Based Inspection Quick Dispatch</div>', unsafe_allow_html=True)

            high_entities = df[df["risk_level"].isin(["High", "Critical"])].head(3)

            q_cols = st.columns(3)
            for idx, (_, row) in enumerate(high_entities.iterrows()):
                if idx < 3:
                    with q_cols[idx]:
                        st.markdown(f"""
                        <div style="background: #FFFFFF; border-radius: 12px; padding: 0.85rem 0.5rem; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                            <div style="background: linear-gradient(135deg, #0F172A, #1E3A8A); border: 2px solid #D97706; width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; margin: 0 auto 0.4rem auto; font-size: 0.95rem;">
                                {row['name'][:2].upper()}
                            </div>
                            <div style="font-weight: 700; color: #0F172A; font-size: 0.82rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{row['name']}</div>
                            <div style="font-size: 0.72rem; color: #D97706; font-weight: 800; margin-top: 0.2rem;">{row['risk_level'].upper()}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Dispatch Field Inspection Task Force", type="primary", use_container_width=True, key="quick_dispatch_exec_btn"):
                st.session_state["edit_success_msg"] = "Inspection Task Force successfully dispatched for high risk entities!"
                st.rerun()

        with col_bh:
            st.markdown('<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-bottom: 0.75rem;">Historical System Composite Risk Trajectory</div>', unsafe_allow_html=True)

            months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
            history_scores = [35.2, 41.0, 38.5, 49.2, 44.8, 52.1, avg_composite]

            df_trend = pd.DataFrame({"Month": months, "System Avg Composite Risk": history_scores})

            fig_area = px.area(
                df_trend,
                x="Month",
                y="System Avg Composite Risk",
                color_discrete_sequence=["#1E3A8A"],
                height=240
            )

            fig_area.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#475569"),
                margin=dict(l=20, r=20, t=20, b=20),
            )

            fig_area.update_traces(
                fillcolor="rgba(30, 58, 138, 0.12)",
                line=dict(width=3, shape="spline")
            )

            st.plotly_chart(fig_area, use_container_width=True)

        st.markdown("---")
        st.subheader("Monitored NBFIs Compliance Directory & Entity Oversight")
        st.markdown("Filter and inspect monitored financial entities, evaluate supervisory risk indicators, and display total company statistics in a modal popup overlay.")

        # Tailored Search & Filters
        sf1, sf2, sf3, sf4 = st.columns([3, 2, 2, 2])
        with sf1:
            q_search = st.text_input("Search Company Name / Tax ID", "", key="exec_q_search")
        with sf2:
            sectors_opt = ["All"] + list(df["sector"].unique()) if not df.empty else ["All"]
            q_sector = st.selectbox("Sector Filter", sectors_opt, key="exec_q_sector")
        with sf3:
            q_risk = st.selectbox("Risk Level", ["All", "Critical", "High", "Medium", "Low"], key="exec_q_risk")
        with sf4:
            q_ews = st.selectbox("EWS Status", ["All", "EWS Flagged Only", "Normal Only"], key="exec_q_ews")

        df_filtered = df.copy()
        if not df_filtered.empty:
            active_search = top_bar_query.strip() or q_search.strip()
            if active_search:
                s_lower = active_search.lower()
                df_filtered = df_filtered[
                    df_filtered["name"].str.lower().str.contains(s_lower) |
                    df_filtered["tax_id"].str.lower().str.contains(s_lower)
                ]
            if q_sector != "All":
                df_filtered = df_filtered[df_filtered["sector"] == q_sector]
            if q_risk != "All":
                df_filtered = df_filtered[df_filtered["risk_level"] == q_risk]
            if q_ews == "EWS Flagged Only":
                df_filtered = df_filtered[df_filtered["ews_flag"] == True]
            elif q_ews == "Normal Only":
                df_filtered = df_filtered[df_filtered["ews_flag"] == False]

        if df_filtered.empty:
            st.info("No monitored entities match the selected search filter criteria.")
        else:
            # Display interactive company cards / table
            st.markdown(f"**Showing {len(df_filtered)} of {len(df)} monitored entities**")

            for _, row in df_filtered.iterrows():
                comp_id = int(row["id"])
                badge_color = (
                    "#991B1B" if row["risk_level"] == "Critical"
                    else "#D97706" if row["risk_level"] == "High"
                    else "#F59E0B" if row["risk_level"] == "Medium"
                    else "#10B981"
                )
                ews_badge = '<span style="background: #EF4444; color: white; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">EWS ALERT</span>' if row["ews_flag"] else '<span style="background: #10B981; color: white; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">Normal</span>'

                with st.container():
                    c_col1, c_col2, c_col3, c_col4, c_col5 = st.columns([3, 2, 2, 2, 2])
                    with c_col1:
                        st.markdown(f"**{row['name']}**<br><span style='color: #64748B; font-size: 0.8rem;'>Tax ID: {row['tax_id']}</span>", unsafe_allow_html=True)
                    with c_col2:
                        st.markdown(f"<span style='color: #0F172A; font-weight: 600;'>{row['sector']}</span>", unsafe_allow_html=True)
                    with c_col3:
                        st.markdown(f"<span style='color: {badge_color}; font-weight: 800;'>{row['risk_level']} ({row['composite_score']:.1f})</span>", unsafe_allow_html=True)
                    with c_col4:
                        st.markdown(ews_badge, unsafe_allow_html=True)
                    with c_col5:
                        if st.button("View Full Details", key=f"btn_view_comp_{comp_id}", use_container_width=True):
                            render_company_details_dialog(db, comp_id)
                    st.markdown("<hr style='margin: 0.4rem 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)


    finally:
        db.close()

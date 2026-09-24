import streamlit as st
from datetime import datetime
from models import Notification
from utils.security import sanitize_input

def create_notification(db, title, message, notif_type="info", user_id=None):
    """
    Creates a new system notification.
    notif_type: 'info', 'warning', 'critical', 'success'
    """
    notif = Notification(
        title=sanitize_input(title),
        message=sanitize_input(message),
        type=notif_type,
        user_id=user_id,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()
    return notif

def get_user_notifications(db, user, unread_only=False):
    """
    Fetch notifications relevant to the logged-in user.
    """
    query = db.query(Notification)
    if user:
        query = query.filter((Notification.user_id == user.id) | (Notification.user_id == None))
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).all()

def mark_as_read(db, notification_id):
    """
    Mark a notification as read.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()

def mark_all_as_read(db, user):
    """
    Mark all unread notifications for a user as read.
    """
    notifs = get_user_notifications(db, user, unread_only=True)
    for n in notifs:
        n.is_read = True
    db.commit()

def render_notification_center_ui(db, user):
    """
    Renders a clean top notification summary banner/expander in English.
    """
    unread_notifs = get_user_notifications(db, user, unread_only=True)
    count = len(unread_notifs)
    
    col1, col2 = st.columns([0.82, 0.18])
    with col1:
        if count > 0:
            st.warning(f"Real-Time Notification Center: You have {count} unread regulatory alerts requiring attention.")
        else:
            st.info("Real-Time Notification Center: No pending alerts. All systems operating within normal parameters.")
            
    with col2:
        with st.popover("Notification Center"):
            st.markdown("#### Regulatory Notifications")
            all_notifs = get_user_notifications(db, user, unread_only=False)[:10]
            
            if not all_notifs:
                st.caption("No notifications recorded.")
            else:
                if count > 0:
                    if st.button("Mark All as Read", key="btn_mark_all_read"):
                        mark_all_as_read(db, user)
                        st.rerun()
                
                st.divider()
                for notif in all_notifs:
                    status_prefix = "[NEW] " if not notif.is_read else ""
                    type_label = {
                        "critical": "CRITICAL",
                        "warning": "WARNING",
                        "info": "INFO",
                        "success": "SUCCESS"
                    }.get(notif.type, "NOTICE")
                    
                    st.markdown(f"**{status_prefix}[{type_label}] {notif.title}**")
                    st.caption(f"{notif.created_at.strftime('%Y-%m-%d %H:%M')} | {notif.message}")
                    if not notif.is_read:
                        if st.button(f"Mark Read #{notif.id}", key=f"read_notif_{notif.id}"):
                            mark_as_read(db, notif.id)
                            st.rerun()
                    st.divider()

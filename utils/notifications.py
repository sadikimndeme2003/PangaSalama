"""Kutengeneza arifa (notifications) kwa watumiaji. Kutofaulu kutuma arifa
hakupaswi kamwe kuvunja kitendo kikuu (kuomba chumba, kubadilisha status,
n.k) -- ndiyo maana kila kitu hapa kimefungwa kwenye try/except."""


def notify(sb, user_id, message, link=None):
    if not user_id:
        return
    try:
        sb.table("notifications").insert({
            "user_id": user_id,
            "message": message,
            "link": link,
        }).execute()
    except Exception:
        pass


def notify_admins(sb, message, link=None):
    try:
        users = sb.auth.admin.list_users(page=1, per_page=1000)
    except Exception:
        return
    for u in users:
        meta = u.user_metadata or {}
        if meta.get("role") == "admin":
            notify(sb, u.id, message, link)

from flask import Blueprint, render_template, session, flash, redirect, url_for
from extensions.supabase_client import get_supabase
from utils.auth_utils import login_required

notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/")
@login_required
def my_notifications():
    sb = get_supabase()
    user_id = session["user_id"]

    try:
        notifs = (
            sb.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
            .data
            or []
        )
    except Exception as e:
        flash(f"Imeshindwa kupakia arifa: {e}", "error")
        return render_template("notifications.html", notifications=[])

    # Mtu akiwa ameona ukurasa huu, arifa zote zinahesabika kama zimesomwa.
    unread_ids = [n["id"] for n in notifs if not n["is_read"]]
    if unread_ids:
        try:
            sb.table("notifications").update({"is_read": True}).in_("id", unread_ids).execute()
            # Badge ya nav (unread_notifications_count) ime-cache kwa 60s
            # (angalia app.py) -- tunaifuta hapa ili ionekane 0 mara moja
            # badala ya kusubiri cache iishe.
            session.pop("unread_count_cache", None)
        except Exception:
            pass

    return render_template("notifications.html", notifications=notifs)


@notification_bp.route("/<notif_id>/delete", methods=["POST"])
@login_required
def delete_notification(notif_id):
    """Futa arifa MOJA. Imefungwa kwa .eq('user_id', ...) pia (si id peke
    yake) ili mtumiaji asiweze kufuta arifa ya mtu mwingine kwa kubadilisha
    ID kwenye URL."""
    sb = get_supabase()
    try:
        sb.table("notifications").delete().eq("id", notif_id).eq("user_id", session["user_id"]).execute()
    except Exception:
        flash("Imeshindwa kufuta arifa.", "error")
    return redirect(url_for("notification.my_notifications"))


@notification_bp.route("/delete-read", methods=["POST"])
@login_required
def delete_read_notifications():
    """Futa arifa ZOTE ambazo tayari zimesomwa (is_read=true) za mtumiaji
    huyu -- kitufe cha 'Futa Zilizosomwa Zote' kwenye ukurasa wa arifa."""
    sb = get_supabase()
    try:
        sb.table("notifications").delete().eq("user_id", session["user_id"]).eq("is_read", True).execute()
    except Exception:
        flash("Imeshindwa kufuta arifa.", "error")
    return redirect(url_for("notification.my_notifications"))

from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions.supabase_client import get_supabase
from utils.auth_utils import role_required, get_users_map
from utils.notifications import notify

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@role_required("admin")
def dashboard():
    """
    Dashibodi ya admin -- inaonyesha tu takwimu 3 za msingi (maombi
    yanayosubiri, vyumba vinavyopatikana, vyumba vilivyochukuliwa/booked).
    Orodha za "hivi karibuni" (maombi/vyumba) ziliondolewa -- admin
    anazipata kikamilifu zaidi kwenye /admin/requests na /admin/rooms.
    """
    sb = get_supabase()
    pending = (
        sb.table("requests").select("*", count="exact").eq("status", "pending").execute()
    )
    rooms_available = (
        sb.table("rooms").select("*", count="exact").eq("status", "available").execute()
    )
    rooms_booked = (
        sb.table("rooms").select("*", count="exact").eq("status", "booked").execute()
    )

    return render_template(
        "admin/dashboard.html",
        pending_count=pending.count or 0,
        available_count=rooms_available.count or 0,
        booked_count=rooms_booked.count or 0,
    )


@admin_bp.route("/rooms")
@role_required("admin")
def rooms_list():
    """
    Vyumba vyote (available/requested/pending_payment/booked/archived).
    'archived' ndiyo vyumba vilivyoshakamilika/kuchukuliwa -- vimetolewa
    kwenye orodha ya umma lakini bado vinaonekana hapa kwa historia.
    """
    sb = get_supabase()

    status_filter = request.args.get("status", "").strip()
    query = sb.table("rooms").select("*")
    if status_filter:
        query = query.eq("status", status_filter)

    rooms = query.order("created_at", desc=True).execute().data or []

    return render_template("admin/rooms.html", rooms=rooms, status_filter=status_filter)


@admin_bp.route("/requests")
@role_required("admin")
def requests_list():
    """Maombi yote -- YALIYOFUTWA (cancelled) hayaonyeshwi hapa kabisa,
    ili orodha ibaki na maombi yanayohitaji hatua tu."""
    sb = get_supabase()
    reqs = (
        sb.table("requests")
        .select(
            "*, rooms(title, area, price, room_type, distance_to_college, "
            "contact_phone, owner_name, owner_id)"
        )
        .neq("status", "cancelled")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    # Hakuna jedwali letu la "users" -- taarifa za mteja (jina/simu) zinatoka
    # moja kwa moja kwenye Supabase Auth (auth.users), lakini tunazipata kwa
    # ombi MOJA (list_users) badala ya ombi moja kwa kila mteja (angalia
    # get_users_map -- inazuia N+1 queries).
    users_map = get_users_map(sb, [r["client_id"] for r in reqs if r.get("client_id")])
    for r in reqs:
        r["client_info"] = users_map.get(r.get("client_id"))

    return render_template("admin/requests.html", requests=reqs)


@admin_bp.route("/requests/<request_id>/status", methods=["POST"])
@role_required("admin")
def update_status(request_id):
    """
    Admin ndiye anayebadilisha hali ya ombi mkono kwa mkono, baada ya
    kuzungumza na mteja na mwenye nyumba nje ya mfumo (simu/WhatsApp):

    pending -> connected (admin ameunganisha mteja na mwenye nyumba; hatua hii
               pia inajumuisha "malipo yanaendelea" -- hazikutenganishwa tena
               kuwa hatua mbili tofauti, ili kupunguza click za admin)
             -> booked (malipo yamekamilika, chumba kimechukuliwa)
             -> cancelled (mteja au mwenye nyumba wamejitoa)

    Chumba kinapofikia 'booked', kinaondolewa kwenye orodha ya umma
    (status ya room inakuwa 'archived').
    """
    sb = get_supabase()
    new_status = request.form.get("status")
    admin_notes = request.form.get("admin_notes", "").strip()

    valid_statuses = ["pending", "connected", "booked", "cancelled"]
    if new_status not in valid_statuses:
        flash("Hali isiyotambulika.", "error")
        return redirect(url_for("admin.requests_list"))

    req_res = sb.table("requests").select("*").eq("id", request_id).limit(1).execute()
    if not req_res.data:
        flash("Ombi halikupatikana.", "error")
        return redirect(url_for("admin.requests_list"))

    req = req_res.data[0]

    update_data = {"status": new_status}
    if admin_notes:
        update_data["admin_notes"] = admin_notes
    sb.table("requests").update(update_data).eq("id", request_id).execute()

    status_messages = {
        "connected": "Umeunganishwa na mwenye chumba. Malipo yakianza kuendelea, msimamizi atakupa maelekezo zaidi.",
        "booked": "Hongera! Chumba chako kimepatikana.",
        "cancelled": "Samahani, ombi lako limefutwa.",
    }
    if new_status in status_messages and req.get("client_id"):
        notify(sb, req["client_id"], status_messages[new_status], link="/requests/mine")

    if req.get("room_id"):
        if new_status == "booked":
            # Chumba kimechukuliwa -> kinaondoka kabisa kwenye orodha ya umma
            sb.table("rooms").update({"status": "archived"}).eq("id", req["room_id"]).execute()
        elif new_status == "cancelled":
            # Ombi limekufa -> chumba kinarudi sokoni
            sb.table("rooms").update({"status": "available"}).eq("id", req["room_id"]).execute()

    flash("Hali ya ombi imesasishwa.", "success")
    return redirect(url_for("admin.requests_list"))

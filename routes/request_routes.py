from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions.supabase_client import get_supabase
from utils.auth_utils import role_required
from utils.validation import validate_price, validate_distance, validate_text_len, validate_area
from utils.notifications import notify, notify_admins
from utils.constants import AREAS

request_bp = Blueprint("request", __name__)


@request_bp.route("/room/<room_id>", methods=["POST"])
@role_required("client")
def request_room(room_id):
    sb = get_supabase()

    room_res = sb.table("rooms").select("*").eq("id", room_id).limit(1).execute()
    if not room_res.data:
        flash("Chumba hiki hakipo tena.", "error")
        return redirect(url_for("main.browse"))

    room = room_res.data[0]

    # Kama HUYU HUYU mteja tayari ana ombi la chumba hiki (mfano: alibonyeza
    # kitufe mara mbili, au akarudi nyuma kwenye browser na kutuma tena),
    # tumwambie ombi lake tayari lipo -- ISIONYESHE ujumbe wa "mteja
    # mwingine ameomba", kwa sababu si kweli: ni ombi lake mwenyewe.
    existing_own = (
        sb.table("requests")
        .select("id")
        .eq("room_id", room_id)
        .eq("client_id", session["user_id"])
        .in_("status", ["pending", "connected", "booked"])
        .limit(1)
        .execute()
    )
    if existing_own.data:
        flash("Umekwisha omba chumba hiki tayari. Subiri msimamizi akuunganishe.", "success")
        return redirect(url_for("request.my_requests"))

    if room["status"] != "available":
        flash("Chumba hiki tayari kimeombwa na mteja mwingine.", "error")
        return redirect(url_for("main.room_detail", room_id=room_id))

    # Update yenye SHARTI (status lazima liwe 'available' wakati huohuo) --
    # inazuia wateja wawili kuomba chumba kimoja kwa wakati mmoja (race
    # condition): kama mtu mwingine ameshapata chumba kabla, hii inarudisha
    # rows 0 na hatuendelei, badala ya kutegemea tu hundi ya juu (ambayo
    # peke yake haitoshi kama maombi mawili yanafika karibu wakati mmoja).
    #
    # Tunaomba count="exact" badala ya kutegemea tu .data: baadhi ya
    # mipangilio ya Supabase client hairudishi safu zilizobadilishwa
    # (.data) baada ya UPDATE (Prefer: return=minimal), hata kama update
    # imefanikiwa -- hilo lilikuwa likisababisha mtu anayeomba kwa mara ya
    # kwanza (kihalali) kuonyeshwa kimakosa ujumbe wa "mteja mwingine
    # ameshaomba". count huja kutoka Content-Range header, hivyo ni ya
    # kutegemewa zaidi bila kujali "representation" preference iliyowekwa.
    claim_res = (
        sb.table("rooms")
        .update({"status": "requested"}, count="exact")
        .eq("id", room_id)
        .eq("status", "available")
        .execute()
    )
    claimed = bool(claim_res.data) or bool(claim_res.count)
    if not claimed:
        flash("Chumba hiki tayari kimeombwa na mteja mwingine.", "error")
        return redirect(url_for("main.room_detail", room_id=room_id))

    sb.table("requests").insert({
        "request_type": "room_request",
        "room_id": room_id,
        "client_id": session["user_id"],
        "owner_id": room["owner_id"],
        "status": "pending",
    }).execute()

    notify(sb, room["owner_id"], f"Mteja mpya ameomba chumba chako: \"{room['title']}\".", link="/rooms/mine")
    notify_admins(sb, f"Ombi jipya la chumba: \"{room['title']}\".", link="/admin/requests")

    flash(
        "Ombi lako limetumwa. Msimamizi (admin) atawasiliana nawe hivi karibuni "
        "kukuunganisha na mwenye chumba.",
        "success",
    )
    return redirect(url_for("main.room_detail", room_id=room_id))


def _request_form():
    return render_template("request_room_form.html", areas=AREAS)


@request_bp.route("/new", methods=["GET", "POST"])
@role_required("client")
def custom_request():
    if request.method == "POST":
        sb = get_supabase()

        desired_area = request.form.get("desired_area", "").strip()
        desired_distance = request.form.get("desired_distance", "").strip()
        desired_room_type = request.form.get("desired_room_type", "").strip()
        desired_price = request.form.get("desired_price", "").strip()
        notes = request.form.get("notes", "").strip()

        if not desired_area:
            flash("Tafadhali chagua eneo unalotaka.", "error")
            return _request_form()

        area_err = validate_area(desired_area)
        if area_err:
            flash(area_err, "error")
            return _request_form()

        distance_val, distance_err = validate_distance(desired_distance, required=False)
        if distance_err:
            flash(distance_err, "error")
            return _request_form()

        price_val, price_err = validate_price(desired_price, required=False)
        if price_err:
            flash(price_err, "error")
            return _request_form()

        notes_err = validate_text_len(notes, "Maelezo")
        if notes_err:
            flash(notes_err, "error")
            return _request_form()

        sb.table("requests").insert({
            "request_type": "custom_request",
            "client_id": session["user_id"],
            "desired_area": desired_area,
            "desired_distance": distance_val,
            "desired_room_type": desired_room_type or None,
            "desired_price": price_val,
            "notes": notes,
            "status": "pending",
        }).execute()

        notify_admins(sb, f"Ombi maalum jipya: {desired_area}.", link="/admin/requests")

        flash("Ombi lako limepokelewa. Tutakutafutia chumba kinachofaa.", "success")
        return redirect(url_for("request.my_requests"))

    return _request_form()


TIMELINE_LABELS = ["Ombi Limetumwa", "Umeunganishwa na Mwenye Nyumba / Malipo Yanaendelea", "Chumba Kimepatikana"]


def _timeline_steps(status):
    """Inarudisha orodha ya hatua 3 na hali yake (done/current/upcoming) kwa status husika.
    (Hatua za 'connected' na 'payment_in_progress' zimeunganishwa kuwa moja --
    operesheni ndogo inayosimamiwa na admin mmoja kwa mkono, hivyo hatua ya ziada
    haikuwa na maana kubwa ya ziada, ilikuwa tu click ya ziada kwa admin.)"""
    order = ["pending", "connected", "booked"]
    if status not in order:
        return None  # mfano 'cancelled' -- hatuonyeshi timeline
    idx = order.index(status)  # 0..2, kila moja "current" ni hatua inayofuata baada ya iliyokamilika
    steps = []
    for i, label in enumerate(TIMELINE_LABELS):
        if i <= idx:
            state = "done" if i < idx or status == "booked" else "current"
        else:
            state = "upcoming"
        steps.append({"label": label, "state": state})
    return steps


@request_bp.route("/mine")
@role_required("client")
def my_requests():
    sb = get_supabase()
    reqs = (
        sb.table("requests")
        .select("*, rooms(title, area, price)")
        .eq("client_id", session["user_id"])
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    for r in reqs:
        r["timeline"] = _timeline_steps(r["status"])

    stats = {
        "total": len(reqs),
        "pending": sum(1 for r in reqs if r["status"] == "pending"),
    }

    return render_template("my_requests.html", requests=reqs, stats=stats)

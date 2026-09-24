from flask import Blueprint, render_template, request, jsonify, current_app, session
from extensions.supabase_client import get_supabase
from utils.phone import whatsapp_link, tel_link
from utils.constants import AMENITY_KEYS
from utils.cloudinary_utils import thumbnail_url, detail_image_url, micro_thumb_url

main_bp = Blueprint("main", __name__)

PAGE_SIZE = 9  # vyumba vingapi kwa kila "ukurasa"

SORT_OPTIONS = {
    "newest": ("created_at", True),
    "price_asc": ("price", False),
    "price_desc": ("price", True),
    "distance": ("distance_to_college", False),
}


def _parse_filters(args):
    return {
        "area": args.get("area", "").strip(),
        "room_type": args.get("room_type", "").strip(),
        "max_price": args.get("max_price", "").strip(),
        "max_distance": args.get("max_distance", "").strip(),
        "sort": args.get("sort", "newest").strip() or "newest",
        "amenities": [a for a in args.getlist("amenities") if a in AMENITY_KEYS] if hasattr(args, "getlist")
                     else [a for a in args.get("amenities", []) if a in AMENITY_KEYS],
    }


def _fetch_rooms(filters, page):
    """
    page ni 1-based. Tunachukua PAGE_SIZE + 1 rekodi ili kujua kama
    kuna ukurasa unaofuata, bila kuhitaji query ya pili ya kuhesabu (count).
    """
    sb = get_supabase()

    q = sb.table("rooms").select("*").eq("status", "available")
    if filters["area"]:
        # Eneo sasa linatoka kwenye dropdown ya AREAS (si maandishi huru
        # tena), hivyo tunatumia ulinganifu kamili (eq) badala ya ilike --
        # sahihi zaidi na haraka zaidi (linatumia index).
        q = q.eq("area", filters["area"])
    if filters["room_type"]:
        q = q.eq("room_type", filters["room_type"])
    if filters["max_price"]:
        try:
            q = q.lte("price", float(filters["max_price"]))
        except ValueError:
            pass
    if filters["max_distance"]:
        try:
            q = q.lte("distance_to_college", float(filters["max_distance"]))
        except ValueError:
            pass
    if filters.get("amenities"):
        q = q.contains("amenities", filters["amenities"])

    sort_key = filters.get("sort") if filters.get("sort") in SORT_OPTIONS else "newest"
    order_col, order_desc = SORT_OPTIONS[sort_key]

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE  # rekodi moja ya ziada kugundua "has_more"

    rooms = q.order(order_col, desc=order_desc).range(start, end).execute().data or []

    has_more = len(rooms) > PAGE_SIZE
    rooms = rooms[:PAGE_SIZE]

    for room in rooms:
        media = (
            sb.table("room_media")
            .select("url")
            .eq("room_id", room["id"])
            .eq("media_type", "image")
            .limit(1)
            .execute()
            .data
        )
        room["thumbnail"] = thumbnail_url(media[0]["url"]) if media else None

    return rooms, has_more


@main_bp.route("/")
def home():
    """
    Landing page ya uuzaji -- inaeleza PangaSalama ni nini na inafanya kazi
    vipi. Haitoi tena idadi za takwimu (vyumba/wamiliki/maombi) wala orodha
    ya vyumba moja kwa moja hapa -- vyumba vinaonekana tu kwenye ukurasa wa
    /vyumba baada ya mtu kubonyeza "Tazama Vyumba". Hii inaifanya landing
    page kupakia haraka zaidi (hakuna maswali ya database yanayohitajika).
    """
    return render_template("landing.html")


@main_bp.route("/vyumba")
def browse():
    """Ukurasa wa kuvinjari/kuchuja vyumba (zamani ulikuwa kwenye '/')."""
    filters = _parse_filters(request.args)
    rooms, has_more = _fetch_rooms(filters, page=1)

    return render_template(
        "browse.html",
        rooms=rooms,
        filters=filters,
        has_more=has_more,
        next_page=2,
    )


@main_bp.route("/api/rooms")
def api_rooms():
    """Inatumika na 'Load More' kwenye home page (JavaScript fetch)."""
    filters = _parse_filters(request.args)
    try:
        page = int(request.args.get("page", 2))
    except ValueError:
        page = 2

    rooms, has_more = _fetch_rooms(filters, page=page)

    return jsonify({
        "rooms": rooms,
        "has_more": has_more,
        "next_page": page + 1,
    })


@main_bp.route("/room/<room_id>")
def room_detail(room_id):
    sb = get_supabase()
    room_res = sb.table("rooms").select("*").eq("id", room_id).limit(1).execute()
    if not room_res.data:
        return render_template("404.html"), 404

    room = room_res.data[0]
    media = sb.table("room_media").select("*").eq("room_id", room_id).execute().data or []
    room["images"] = [m for m in media if m["media_type"] == "image"]
    room["videos"] = [m for m in media if m["media_type"] == "video"]
    for img in room["images"]:
        img["display_url"] = detail_image_url(img["url"])
        img["micro_url"] = micro_thumb_url(img["url"])

    # Ongeza "views" -- lakini si kama mwenye chumba mwenyewe ndiye anaeangalia
    # (asije akajipandishia takwimu za chumba chake mwenyewe). Vyumba
    # alivyoweka ADMIN kwa niaba ya mwenye nyumba havina owner_id (None) --
    # kwa hivyo daima ongeza views kwa hivyo vyumba (hakuna "mwenye chumba
    # anayejiangalia" iwezekanavyo).
    if room.get("owner_id") is None or session.get("user_id") != room.get("owner_id"):
        try:
            sb.table("rooms").update({"views": (room.get("views") or 0) + 1}).eq("id", room_id).execute()
        except Exception:
            pass

    # Chumba kikiwa tayari kimeombwa, tunahitaji kujua NI NANI aliyekiomba --
    # ili ujumbe uliomwonyeshwa mtumiaji utofautiane kulingana na yeye ni
    # nani (mteja aliyeomba mwenyewe / mteja mwingine / mwenye nyumba / admin).
    room["requested_by_client_id"] = None
    if room["status"] != "available":
        try:
            req = (
                sb.table("requests")
                .select("client_id")
                .eq("room_id", room_id)
                .in_("status", ["pending", "connected", "booked"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
            if req:
                room["requested_by_client_id"] = req[0]["client_id"]
        except Exception:
            pass

    # Vitufe vya WhatsApp/Simu vinamwelekeza ADMIN (siyo mwenye nyumba) --
    # ndiye daraja pekee kati ya mteja na mwenye nyumba kwenye muundo wetu.
    admin_number = current_app.config.get("ADMIN_WHATSAPP_NUMBER", "")
    wa_message = f"Habari, nimeona chumba cha \"{room['title']}\" huko {room['area']} kwenye PangaSalama. Naomba maelezo zaidi."
    room["whatsapp_url"] = whatsapp_link(admin_number, wa_message) if admin_number else None
    room["tel_url"] = tel_link(admin_number) if admin_number else None

    return render_template("room_detail.html", room=room)

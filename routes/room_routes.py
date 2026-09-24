import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from extensions.supabase_client import get_supabase
from utils.auth_utils import role_required
from utils.validation import validate_price, validate_distance, validate_text_len, validate_area
from utils.constants import AMENITIES, AMENITY_KEYS, AREAS
from postgrest import APIError

room_bp = Blueprint("room", __name__)

ROOM_TYPES = ["single", "shared", "self-contained", "bed-sitter"]


def _post_room_form(**extra):
    return render_template(
        "post_room.html",
        room_types=ROOM_TYPES,
        amenities=AMENITIES,
        areas=AREAS,
        is_admin=session.get("role") == "admin",
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        upload_preset=current_app.config["CLOUDINARY_UPLOAD_PRESET"],
        **extra,
    )


@room_bp.route("/new", methods=["GET", "POST"])
@role_required("owner", "admin")
def new_room():
    is_admin = session.get("role") == "admin"

    if request.method == "POST":
        sb = get_supabase()

        area = request.form.get("area", "").strip()
        distance = request.form.get("distance_to_college", "").strip()
        price = request.form.get("price", "").strip()
        room_type = request.form.get("room_type", "").strip()
        features = request.form.get("features", "").strip()
        contact_phone = request.form.get("contact_phone", "").strip()
        media_json = request.form.get("media_json", "[]")
        selected_amenities = [a for a in request.form.getlist("amenities") if a in AMENITY_KEYS]

        # Admin anapoweka chumba kwa niaba ya mwenye nyumba (asiye na akaunti
        # au simu janja), jina la mwenye nyumba linaandikwa kwa mkono kwenye
        # fomu. Mwenye nyumba anapoweka chumba chake mwenyewe, jina
        # linatoka kwenye akaunti yake moja kwa moja -- hakuna sehemu ya
        # ziada ya kujaza.
        if is_admin:
            owner_name = request.form.get("owner_name", "").strip()
            owner_id = None
        else:
            owner_name = session.get("full_name", "")
            owner_id = session["user_id"]

        if not (area and price and room_type and contact_phone):
            flash("Jaza sehemu zote za lazima.", "error")
            return _post_room_form()

        if is_admin and not owner_name:
            flash("Jaza jina la mwenye nyumba.", "error")
            return _post_room_form()

        if room_type not in ROOM_TYPES:
            flash("Aina ya chumba si sahihi.", "error")
            return _post_room_form()

        area_err = validate_area(area)
        if area_err:
            flash(area_err, "error")
            return _post_room_form()

        price_val, price_err = validate_price(price, required=True)
        if price_err:
            flash(price_err, "error")
            return _post_room_form()

        distance_val, distance_err = validate_distance(distance, required=False)
        if distance_err:
            flash(distance_err, "error")
            return _post_room_form()

        text_err = validate_text_len(features, "Maelezo mengine ya ziada")
        if text_err:
            flash(text_err, "error")
            return _post_room_form()

        try:
            media_items = json.loads(media_json)
        except (ValueError, TypeError):
            media_items = []

        # Hakuna "kichwa cha tangazo" cha kuandika tena -- linatengenezwa
        # lenyewe kutoka aina ya chumba + eneo (mfano "Chumba cha Single -
        # Kitefure"), ili kupunguza hatua kwa mwenye nyumba/admin.
        title = f"Chumba cha {room_type.capitalize()} - {area}"

        try:
            room_res = sb.table("rooms").insert({
                "owner_id": owner_id,
                "owner_name": owner_name,
                "title": title,
                "area": area,
                "distance_to_college": distance_val,
                "price": price_val,
                "room_type": room_type,
                "features": features,
                "amenities": selected_amenities,
                "contact_phone": contact_phone,
                "status": "available",
            }).execute()
        except APIError as e:
            hint = f" ({e.hint})" if getattr(e, "hint", None) else ""
            flash(f"Imeshindwa kuhifadhi chumba: {e.message}{hint}", "error")
            return _post_room_form()
        except Exception as e:
            flash(f"Hitilafu isiyotarajiwa (chumba): {e}", "error")
            return _post_room_form()

        room_id = room_res.data[0]["id"]

        # Picha/video ZILISHAPAKIWA Cloudinary na browser moja kwa moja (JS).
        # Hapa tunahifadhi tu links zilizorudi -- si faili nzima -- ndiyo maana
        # hatua hii ni ya haraka. Chumba kishatengenezwa, hivyo hata media
        # ikishindwa hapa, chumba tayari kipo -- tunamuonya mmiliki tu.
        media_errors = 0
        for item in media_items:
            url = item.get("url")
            public_id = item.get("public_id")
            media_type = item.get("type")
            if url and public_id and media_type in ("image", "video"):
                try:
                    sb.table("room_media").insert({
                        "room_id": room_id,
                        "url": url,
                        "media_type": media_type,
                        "public_id": public_id,
                    }).execute()
                except Exception:
                    media_errors += 1

        if media_errors:
            flash(
                f"Chumba kimehifadhiwa, lakini picha/video {media_errors} hazikuhifadhika vizuri.",
                "error",
            )
        else:
            flash("Chumba kimewekwa kikisubiri wateja.", "success")

        return redirect(url_for("admin.rooms_list") if is_admin else url_for("room.my_rooms"))

    return _post_room_form()


@room_bp.route("/mine")
@role_required("owner")
def my_rooms():
    sb = get_supabase()
    rooms = (
        sb.table("rooms")
        .select("*")
        .eq("owner_id", session["user_id"])
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    return render_template("my_rooms.html", rooms=rooms)

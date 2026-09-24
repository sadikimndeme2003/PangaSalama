from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions.supabase_client import get_supabase
from supabase import AuthApiError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "client")  # "owner" au "client"

        if role not in ("owner", "client"):
            role = "client"

        if not (full_name and email and phone and password):
            flash("Tafadhali jaza sehemu zote.", "error")
            return render_template("register.html")

        sb = get_supabase()

        try:
            result = sb.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "phone": phone,
                        "role": role,
                    }
                },
            })
        except AuthApiError as e:
            flash(f"Usajili umeshindikana: {e.message}", "error")
            return render_template("register.html")

        # Kama "Confirm email" imezimwa kwenye Supabase Auth settings,
        # sign_up inarudisha session moja kwa moja -> tunamuingiza papo hapo.
        if result.session and result.user:
            session["user_id"] = result.user.id
            session["email"] = result.user.email
            session["full_name"] = full_name
            session["role"] = role
            flash(f"Karibu, {full_name}! Usajili umefanikiwa.", "success")
            if role == "owner":
                return redirect(url_for("room.my_rooms"))
            return redirect(url_for("main.browse"))

        # Confirm email ikiwa imewashwa, mtumiaji lazima athibitishe kwa barua pepe kwanza
        flash(
            "Usajili umepokelewa. Angalia barua pepe yako uthibitishe akaunti "
            "kabla ya kuingia.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        sb = get_supabase()

        try:
            result = sb.auth.sign_in_with_password({"email": email, "password": password})
        except AuthApiError:
            flash("Barua pepe au nenosiri sio sahihi.", "error")
            return render_template("login.html")

        user = result.user
        meta = user.user_metadata or {}

        session["user_id"] = user.id
        session["email"] = user.email
        session["full_name"] = meta.get("full_name", user.email)
        session["role"] = meta.get("role", "client")

        flash(f"Karibu tena, {session['full_name']}!", "success")

        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        if session["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        if session["role"] == "owner":
            return redirect(url_for("room.my_rooms"))
        return redirect(url_for("main.browse"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    session.clear()
    flash("Umetoka kwenye akaunti yako.", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Badala ya barua pepe/link, mtumiaji anathibitishwa kwa barua pepe + namba
    ya simu aliyosajili nazo, kisha anaweka nenosiri jipya papo hapo.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        new_password = request.form.get("new_password", "")

        if not (email and phone and new_password):
            flash("Jaza sehemu zote.", "error")
            return render_template("forgot_password.html")

        sb = get_supabase()

        matched_user = None
        try:
            users = sb.auth.admin.list_users(page=1, per_page=1000)
            for u in users:
                meta = u.user_metadata or {}
                if u.email and u.email.lower() == email and meta.get("phone", "").strip() == phone:
                    matched_user = u
                    break
        except Exception:
            matched_user = None

        if not matched_user:
            flash("Taarifa hizo hazifanani na akaunti yoyote iliyosajiliwa.", "error")
            return render_template("forgot_password.html")

        try:
            sb.auth.admin.update_user_by_id(matched_user.id, {"password": new_password})
        except AuthApiError as e:
            flash(f"Imeshindwa kubadilisha nenosiri: {e.message}", "error")
            return render_template("forgot_password.html")

        flash("Nenosiri limebadilishwa. Sasa ingia na nenosiri jipya.", "success")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")

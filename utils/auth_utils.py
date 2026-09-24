from functools import wraps
from flask import session, redirect, url_for, flash, request


def current_user():
    """Inarudisha dict rahisi ya mtumiaji aliye-login kutoka session, au None.

    Chanzo cha ukweli ni Supabase Auth (auth.users) -- session hii ya Flask
    ni nakala nyepesi tu ya kile Supabase kilichorudisha wakati wa login,
    ili tusihitaji kupiga Supabase kwa kila request.
    """
    if "user_id" not in session:
        return None
    return {
        "id": session.get("user_id"),
        "full_name": session.get("full_name"),
        "email": session.get("email"),
        "role": session.get("role"),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Tafadhali ingia kwenye akaunti yako kwanza.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def get_users_map(sb, user_ids):
    """
    Inarudisha dict {user_id: {"full_name", "email", "phone"}} kwa orodha ya
    user_ids uliyotoa.

    Kabla, kurasa za admin (dashboard, rooms, requests) zilikuwa zinapiga
    sb.auth.admin.get_user_by_id() KILA MSTARI (N+1 queries) -- ikiwa na
    maombi/vyumba 50, hiyo ni maombi 50 tofauti kwenda Supabase Auth kwa kila
    ufunguzi wa ukurasa. Hapa tunapiga list_users() MARA MOJA TU, kisha
    tunachagua tu wale tunaowahitaji kwenye kumbukumbu (memory) -- haraka
    zaidi na hailegezi Supabase kadri data inavyoongezeka.

    (Kama watumiaji wakizidi 1000, ongeza ukurasa wa pili hapa -- kwa sasa
    per_page=1000 inatosha kwa ukubwa wa mfumo huu.)
    """
    if not user_ids:
        return {}
    wanted = set(user_ids)
    result = {}
    try:
        users_res = sb.auth.admin.list_users(page=1, per_page=1000)
        for u in users_res:
            if u.id in wanted:
                meta = u.user_metadata or {}
                result[u.id] = {
                    "full_name": meta.get("full_name", u.email),
                    "email": u.email,
                    "phone": meta.get("phone", ""),
                }
    except Exception:
        pass
    return result


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Tafadhali ingia kwenye akaunti yako kwanza.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if session.get("role") not in roles:
                flash("Huna ruhusa ya kufikia ukurasa huu.", "error")
                return redirect(url_for("main.browse"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

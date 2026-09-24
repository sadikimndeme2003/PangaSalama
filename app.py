import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_wtf import CSRFProtect
from config import Config

load_dotenv()

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # --- Usalama wa session cookie ---
    app.config["SESSION_COOKIE_HTTPONLY"] = True   # JS haiwezi kusoma cookie ya session
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # kinga dhidi ya CSRF ya msingi
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") != "development"
    # ^ Vercel ni HTTPS kila wakati, hivyo True kwa default; tunaiacha False tu
    #   ukiwa unaendesha localhost bila HTTPS (FLASK_ENV=development kwenye .env).

    csrf.init_app(app)

    from utils.constants import AMENITY_MAP, AREAS
    app.jinja_env.globals["AMENITY_MAP"] = AMENITY_MAP
    app.jinja_env.globals["AREAS"] = AREAS

    from markupsafe import Markup

    def icon(name, cls=""):
        """Inatengeneza <svg><use> inayorejelea sprite iliyo ndani ya ukurasa
        wenyewe (templates/_icons_sprite.html, imejumuishwa mara moja
        kwenye base.html) -- badala ya Font Awesome CDN (nzito kwa data ya
        simu). Awali sprite ilikuwa faili tofauti (static/icons-sprite.svg)
        iliyorejelewa kwa URL, lakini baadhi ya browser/webview (k.m.
        "Desktop mode" kwenye simu) hazitegemewi vizuri kwa <use> ya
        cross-document -- icon huonekana tofauti au haionekani kabisa.
        Kuiweka ndani ya ukurasa (same-document fragment #icon-jina)
        kunaondoa tatizo hilo kabisa katika browser zote."""
        cls_attr = f"icon {cls}".strip()
        return Markup(
            f'<svg class="{cls_attr}" aria-hidden="true">'
            f'<use href="#icon-{name}"></use></svg>'
        )

    app.jinja_env.globals["icon"] = icon

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.room_routes import room_bp
    from routes.request_routes import request_bp
    from routes.admin_routes import admin_bp
    from routes.notification_routes import notification_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(room_bp, url_prefix="/rooms")
    app.register_blueprint(request_bp, url_prefix="/requests")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(notification_bp, url_prefix="/notifications")

    @app.context_processor
    def inject_helpers():
        import time
        from flask import session
        from utils.auth_utils import current_user

        # Idadi ya arifa zisizosomwa inahitajika KWENYE KILA UKURASA (badge
        # kwenye nav), lakini kabla ilikuwa inapiga Supabase kwa KILA request
        # hata kama mtumiaji haangalii arifa kabisa. Hapa tunaicache kwenye
        # session kwa dakika moja (60s) -- inapunguza sana maombi kwenda
        # database bila kuathiri sana uzoefu wa mtumiaji (badge inachelewa
        # sekunde chache tu kusasishwa, si tatizo kwa arifa zisizo za dharura).
        UNREAD_CACHE_TTL = 60
        unread_count = 0
        if session.get("user_id"):
            cached = session.get("unread_count_cache")
            now = time.time()
            if cached and (now - cached.get("ts", 0)) < UNREAD_CACHE_TTL:
                unread_count = cached.get("count", 0)
            else:
                try:
                    from extensions.supabase_client import get_supabase
                    sb = get_supabase()
                    res = (
                        sb.table("notifications")
                        .select("id", count="exact")
                        .eq("user_id", session["user_id"])
                        .eq("is_read", False)
                        .execute()
                    )
                    unread_count = res.count or 0
                    session["unread_count_cache"] = {"count": unread_count, "ts": now}
                except Exception:
                    pass

        return {"current_user": current_user(), "unread_notifications_count": unread_count}

    @app.errorhandler(Exception)
    def handle_any_error(e):
        from werkzeug.exceptions import HTTPException

        if isinstance(e, HTTPException):
            return e

        if app.config.get("DEBUG_ERRORS"):
            import traceback
            tb = traceback.format_exc()
            html = (
                "<h1 style='color:#b91c1c'>DEBUG_ERRORS imewashwa -- traceback halisi</h1>"
                "<p style='color:#b91c1c'>ZIMA DEBUG_ERRORS baada ya ku-debug (Vercel env vars).</p>"
                f"<pre style='white-space:pre-wrap;background:#f1f5f9;padding:16px;border-radius:8px'>{tb}</pre>"
            )
            return html, 500

        app.logger.exception(e)
        return render_template("500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

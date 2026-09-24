import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_badilisha")

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    # Preset isiyo-tiwa-saini (unsigned) -- inaruhusu simu ya mwenye chumba
    # kupakia picha/video MOJA KWA MOJA kwenda Cloudinary (bila kupitia server
    # yetu ya Vercel). Hii inaepusha: (1) kikomo cha ukubwa wa request kwenye
    # Vercel free tier, (2) ucheleweshaji wa kupitisha faili mara mbili.
    CLOUDINARY_UPLOAD_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "")

    # Bado tunaitumia hii kwa maombi madogo ya text (JSON ya media_json baada
    # ya kupakia Cloudinary), si kwa faili nzima tena.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB kwa request ya form (text tu)

    # Namba ya WhatsApp ya ADMIN (siyo ya mwenye nyumba). Kwa muundo wetu,
    # admin ndiye daraja pekee kati ya mteja na mwenye nyumba, hivyo vitufe
    # vya "Piga Simu"/"WhatsApp" kwenye ukurasa wa chumba vinamwelekeza
    # admin, siyo mwenye nyumba moja kwa moja.
    ADMIN_WHATSAPP_NUMBER = os.environ.get("ADMIN_WHATSAPP_NUMBER", "")

    # Ukiwasha hii (DEBUG_ERRORS=true kwenye Vercel), error yoyote itaonyesha
    # traceback halisi ya Python moja kwa moja kwenye browser badala ya ukurasa
    # wa jumla wa "Internal Server Error" -- muhimu kwa ku-debug haraka bila
    # Vercel logs. ZIMA (futa variable hii au weka false) mara tatizo likiisha,
    # kwa sababu traceback inaweza kuonyesha maelezo nyeti ya code/mazingira.
    DEBUG_ERRORS = os.environ.get("DEBUG_ERRORS", "false").strip().lower() == "true"

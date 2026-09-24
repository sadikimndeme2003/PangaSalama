"""
Kihifadhi cha picha/video kupitia Cloudinary (free tier: ~25GB storage,
25GB bandwidth kwa mwezi -- inatosha kuanzia).

Kwa nini Cloudinary badala ya kuhifadhi faili moja kwa moja kwenye
Vercel: Vercel serverless functions hazina disk ya kudumu (kila
request inaweza kuja kwenye server tofauti), kwa hiyo picha/video
LAZIMA zihifadhiwe mahali pa nje (Cloudinary / Supabase Storage).
"""
import os
import cloudinary
import cloudinary.uploader

_configured = False


def _configure():
    global _configured
    if not _configured:
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True,
        )
        _configured = True


def upload_room_media(file_storage, room_id, resource_type="image"):
    """
    file_storage: werkzeug FileStorage (kutoka request.files)
    resource_type: "image" au "video"
    Returns dict: {"url": ..., "public_id": ..., "type": resource_type}
    """
    _configure()
    result = cloudinary.uploader.upload(
        file_storage,
        folder=f"vyumba/{room_id}",
        resource_type=resource_type,
        # video kubwa zinabanwa kiasi ili zisitumie bandwidth nyingi kwenye free tier
        eager=[{"quality": "auto"}] if resource_type == "image" else None,
    )
    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "type": resource_type,
    }


def delete_room_media(public_id, resource_type="image"):
    _configure()
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)


def resized_url(url, transformation):
    """
    Inaingiza Cloudinary transformation (mfano 'w_400,q_auto,f_auto') kwenye
    URL ya picha, mara baada ya '/upload/'. Hii inapunguza SANA data
    inayopakuliwa na simu -- badala ya kupakua picha kamili (mara nyingi
    2-5MB kutoka kamera ya simu) kwa kadi ndogo ya 160px, mtumiaji anapakua
    toleo dogo tayari-lililobanwa (mara nyingi chini ya 50KB).

    q_auto: Cloudinary inachagua ubora bora kiotomatiki (kupunguza ukubwa
            bila kuathiri sana muonekano).
    f_auto: inachagua muundo bora zaidi kwa browser husika (mfano WebP/AVIF
            badala ya JPEG kwenye simu zinazounga mkono).

    Kama url si Cloudinary URL ya kawaida (haina '/upload/'), inarudisha
    url ile ile bila kubadilika -- salama, haivunji chochote.
    """
    if not url or "/upload/" not in url:
        return url
    return url.replace("/upload/", f"/upload/{transformation}/", 1)


def thumbnail_url(url):
    """Kadi ndogo za orodha (browse, my_rooms, home) -- 400px."""
    return resized_url(url, "w_400,q_auto,f_auto")


def detail_image_url(url):
    """Picha kubwa kwenye ukurasa wa chumba (room_detail) -- 1000px."""
    return resized_url(url, "w_1000,q_auto,f_auto")


def micro_thumb_url(url):
    """Thumbnail ndogo sana (strip ya 64px chini ya picha kuu) -- 150px."""
    return resized_url(url, "w_150,q_auto,f_auto")

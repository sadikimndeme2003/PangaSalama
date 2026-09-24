"""
Supabase client moja unaotumika mfumo mzima.

Tunatumia SERVICE ROLE KEY hapa kwa sababu client zote za DB zinatokea
server-side (ndani ya Flask routes), si browser. Hii inatuepusha na
kuandika RLS policies ngumu wakati wa MVP -- admin (server) ndiye
anaye-manage ruhusa zote kwa mantiki ya application code.

MUHIMU: SUPABASE_SERVICE_KEY isiwahi kuwekwa kwenye kitu chochote
kinachotumwa kwa browser (templates, JS ya frontend, n.k).
"""
import os
from typing import Optional
from supabase import create_client, Client

_client: Optional[Client] = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY hazijawekwa kwenye "
                "environment variables (angalia .env)."
            )
        _client = create_client(url, key)
    return _client

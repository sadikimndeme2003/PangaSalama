"""Sifa za kawaida za chumba (amenities) -- orodha moja inayotumika kwenye
fomu ya kuweka chumba, room cards, na ukurasa wa chumba, ili icons/majina
yasitofautiane mahali tofauti."""

AMENITIES = [
    {"key": "maji", "label": "Maji", "icon": "droplet"},
    {"key": "umeme", "label": "Umeme", "icon": "bolt"},
    {"key": "choo_ndani", "label": "Choo cha Ndani", "icon": "toilet"},
    {"key": "choo_nje", "label": "Choo cha Nje", "icon": "toilet"},
    {"key": "fensi", "label": "Fensi", "icon": "shield-halved"},
    {"key": "parking", "label": "Parking", "icon": "square-parking"},
]

AMENITY_KEYS = {a["key"] for a in AMENITIES}
AMENITY_MAP = {a["key"]: a for a in AMENITIES}

"""Maeneo yaliyopo karibu na Chuo cha Mwenge (MWECAU) -- orodha funge badala
ya maandishi huru, ili utafutaji/uchujaji wa eneo uwe sahihi kila wakati
(hakuna 'Pasua' dhidi ya 'pasua' dhidi ya 'Pasua Mtaa...')."""
AREAS = [
    "Kitefure",
    "Kitefure Msikitini",
    "Swahaba",
    "BM",
    "Doctor Sum",
    "KKT",
    "TAG Endeni",
    "Mponeja",
    "Sabato",
    "Mama Mzanaa",
    "Kifumbu",
    "Marunda",
    "Summit",
    "Mawela",
    "Uru Seminary",
    "White House",
    "Chadema Road",
    "Kwa Change",
]

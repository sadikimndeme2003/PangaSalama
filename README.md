# PangaSalama — Mfumo wa Udalali wa Vyumba

Flask + Supabase (Postgres) + Cloudinary (picha/video) + Vercel (hosting), free-tier.

Jina la mfumo ("PangaSalama") liko kwenye `templates/base.html` (title, navbar, footer) na
`templates/landing.html` (hero) -- ukitaka kubadilisha tena baadaye, ni hapo tu.

## 1. Muundo wa mfumo

- **Owner (mwenye nyumba)**: anajisajili, anaweka chumba (bei, eneo, picha, video, sifa, umbali kutoka chuo).
- **Client (mteja)**: anavinjari/anachuja vyumba, anaomba chumba fulani, au anajaza "ombi maalum" kama hakuna kinachomfaa.
- **Admin (wewe)**: ndiye pekee anayeongea na mteja na mwenye nyumba. Unabadilisha status ya ombi (`/admin/requests`) hadi malipo yakamilike — ndipo chumba kinaondoka kwenye orodha ya umma (`archived`).

**Muhimu kuhusu watumiaji:** mfumo HAUNA jedwali lake la "users". Kila mtu (owner/client/admin) anahifadhiwa moja kwa moja na **Supabase Auth** (`auth.users`) — usajili, login, na password zote zinashughulikiwa na Supabase yenyewe. Jina kamili, namba ya simu, na role (owner/client/admin) vinahifadhiwa kwenye `user_metadata` ya kila akaunti wakati wa usajili, si kwenye jedwali letu.

## 2. Kuandaa Supabase (bure)

1. Fungua akaunti https://supabase.com , unda project mpya.
2. Nenda **SQL Editor** → bandika content ya faili `supabase_schema.sql` iliyopo hapa → Run. Hii inatengeneza tables za `rooms`, `room_media`, `requests` (zinazorejelea `auth.users` moja kwa moja — hakuna jedwali letu la users).
3. Nenda **Project Settings → API Keys** → chukua:
   - `Project URL`
   - `service_role` key (kwa **SUPABASE_SERVICE_KEY**) -- kama unaona chaguo la "Legacy API Keys", tumia hilo toleo la zamani la JWT (linaanza na `eyJ...`), si lile jipya la `sb_secret_...`, kwa sababu baadhi ya shughuli za Auth Admin (kama kutengeneza admin kwa script) hazifanyi kazi vizuri na muundo mpya kwenye maktaba tunayotumia.
4. **Muhimu kwa usajili laini**: nenda **Authentication → Providers → Email** na zima (toggle off) **"Confirm email"** ili mtumiaji aingizwe moja kwa moja baada ya kujisajili, bila kusubiri kuthibitisha barua pepe.

## 3. Kutengeneza akaunti yako ya ADMIN (mara moja tu)

Hakuna usajili wa admin kupitia `/auth/register` kwa makusudi (usalama). Tengeneza admin wako moja kwa moja kwenye Supabase:

1. Supabase → **Authentication → Users** → **Add user → Create new user**
2. Weka barua pepe na password yako, hakikisha **"Auto Confirm User"** imewashwa → **Create**
3. Nenda **SQL Editor**, bandika (badilisha jina/simu/barua pepe):
   ```sql
   update auth.users
   set raw_user_meta_data = raw_user_meta_data || '{"full_name": "Jina Lako", "phone": "0712345678", "role": "admin"}'::jsonb
   where email = 'barua-pepe-yako@mfano.com';
   ```
4. Run. Sasa unaweza ku-login kwenye `/auth/login` na akaunti hiyo, utaingia moja kwa moja kama admin.

## 4. Kuandaa Cloudinary (bure)

1. Fungua akaunti https://cloudinary.com (free tier: ~25GB storage/bandwidth kwa mwezi, inatosha mwanzoni).
2. Kwenye Dashboard, chukua `Cloud Name`, `API Key`, `API Secret`.
3. **Tengeneza "unsigned upload preset"** (hii ni MUHIMU -- ndiyo inayoruhusu simu ya mwenye chumba kupakia picha/video moja kwa moja Cloudinary, badala ya kupitia server yetu -- inaepusha kucheleweshwa/kukwama kwenye mtandao wa simu):
   - Settings (gia) → **Upload** → **Upload presets** → **Add upload preset**
   - **Signing Mode**: chagua **Unsigned**
   - (Hiari) weka **Folder** kuwa `vyumba` ili faili zote zipangwe pamoja
   - (Hiari) weka **Max file size** kikomo cha busara (mfano 15MB) kuzuia video kubwa mno
   - Hifadhi, kisha nakili **jina la preset** -- hii ndiyo `CLOUDINARY_UPLOAD_PRESET`

## 5. Kuweka mazingira (environment variables)

Nakili `.env.example` kuwa `.env`, jaza values zako zote (Supabase, Cloudinary, SECRET_KEY).

**MUHIMU**: `.env` isiwahi kupakiwa GitHub (tayari iko kwenye `.gitignore`).

## 6. Kuendesha kwenye simu (Termux)

```bash
pip install -r requirements.txt --break-system-packages
python app.py                # anzisha server ya majaribio (localhost)
```

**Kumbuka**: `pip install` ya `supabase` wakati mwingine inashindwa kwenye Termux (hasa `pydantic-core`, inayohitaji Rust kujengwa ambayo Termux haina moja kwa moja). Hii haiathiri Vercel (ambako imesakinishwa sahihi) -- ni tatizo la kuendesha app localhost kwenye simu pekee. Kama ukikwama hapa, si tatizo kubwa: `git push`/GitHub bado zinafanya kazi kama kawaida, na unaweza kuendelea moja kwa moja na Vercel (sehemu ya 7).

## 7. Ku-deploy Vercel (bure)

1. Weka project hii kwenye GitHub repo mpya (kutoka Termux: `git init`, `git add .`, `git commit`, `git push`).
2. Kwenye vercel.com, "Import Project" kutoka GitHub repo yako.
3. Kwenye Vercel → Project Settings → Environment Variables, ongeza zile zile ulizoweka kwenye `.env` (SUPABASE_URL, SUPABASE_SERVICE_KEY, CLOUDINARY_*, SECRET_KEY).
4. Deploy. Vercel itatumia `vercel.json` iliyopo kuendesha Flask app moja kwa moja.

## 8. Mtiririko wa matumizi (workflow)

1. Mwenye nyumba anajisajili (`role=owner`) → anaweka chumba (`/rooms/new`), akiambatanisha picha/video (zinapakiwa Cloudinary moja kwa moja). **AU** wewe (admin) unamwekea chumba kwa niaba yake (kwa mwenye nyumba asiye na akaunti/simu janja) -- angalia sehemu ya 13.
2. Mteja anajisajili (`role=client`) → anatafuta vyumba kwenye `/vyumba` → akipenda chumba, anabonyeza "Omba Chumba Hiki" (`status: requested`, halionekani kuombwa na wengine).
3. Wewe (admin) unaona ombi kwenye `/admin/requests` -- pamoja na taarifa za mteja aliyeomba (jina/simu) NA za mwenye nyumba wa chumba hicho (jina/simu) kwenye ombi lilelile -- unawasiliana na pande zote mbili nje ya mfumo (simu/WhatsApp), kisha unabadilisha status: `connected` (inajumuisha "malipo yanaendelea") → `booked`.
4. Chumba kikiwa `booked`, kinatolewa kiotomatiki kwenye orodha ya umma.
5. Ukibofya `cancelled`, chumba kinarudi `available` kiotomatiki.
6. Mtu akisahau nenosiri, anabofya "Umesahau Nenosiri?" kwenye `/auth/login` → anaweka barua pepe + namba ya simu aliyosajili nazo (kama uthibitisho) → anaweka nenosiri jipya moja kwa moja, bila barua pepe wala kiungo.

## 9. Kuhusu usalama wa "role"

Role (`owner`/`client`/`admin`) inahifadhiwa kwenye `user_metadata` ya Supabase Auth. Andiko la server (Flask, likitumia service_role key) ndilo pekee linaloweza kubadilisha `role` au password. Ukurasa wa "Umesahau Nenosiri" unathibitisha mtumiaji kwa barua pepe + simu iliyosajiliwa kabla ya kubadilisha password -- huu ni uthibitisho rahisi tu (siyo salama kama kiungo cha barua pepe halisi), hivyo kama unataka usalama zaidi baadaye, fikiria kurudisha njia ya barua pepe.

## 10. Vitu vya kuongeza baadaye (upgrade)

- Malipo ya moja kwa moja (Mpesa/Tigopesa API) badala ya kushuhudia manually.
- In-app chat kati ya admin na pande zote mbili (badala ya simu/WhatsApp nje ya mfumo).
- Google Maps Distance Matrix API kuhesabu umbali kiotomatiki badala ya mwenye nyumba kuandika mwenyewe.
- Rating/maoni baada ya booking kukamilika.

## 11. Muundo wa faili

```
app.py                     # Flask entrypoint
config.py                  # Env config
vercel.json                # Vercel deployment config
supabase_schema.sql        # Database schema
extensions/supabase_client.py
utils/auth_utils.py        # Login/role decorators, get_users_map (N+1 fix)
utils/cloudinary_utils.py  # Upload wa picha/video + image transformations
utils/constants.py         # AREAS (dropdown ya maeneo), AMENITIES
routes/
  auth_routes.py           # register/login/logout/forgot-password
  main_routes.py           # landing page, browse + filter, room detail
  room_routes.py           # weka chumba (owner AU admin), vyumba vyangu
  request_routes.py        # client: omba chumba, ombi maalum
  admin_routes.py          # admin: dashboard, manage requests/status
static/styles.css          # CSS mahususi (badala ya Tailwind CDN)
templates/_icons_sprite.html  # Icons zote (badala ya Font Awesome CDN)
templates/                 # Jinja2
```

## 12. Sasisho la Hivi Karibuni (uzito kwa simu / mobile-first)

Mabadiliko haya yalifanywa mahususi kupunguza data/CPU inayotumika kwenye
simu (watumiaji wengi ni wa simu, si computa), na kuboresha usahihi wa
utafutaji karibu na MWECAU:

- **Tailwind CDN imeondolewa** -> `static/styles.css` ina CSS ndogo
  iliyojengwa mahususi kwa classes zinazotumika kwenye mradi huu tu.
  Ukiongeza class mpya ya Tailwind kwenye template, itabidi uiongeze
  kwenye `styles.css` pia (haita-generate yenyewe -- si Tailwind halisi).
- **Font Awesome CDN imeondolewa** -> `templates/_icons_sprite.html` ina icons
  46 pekee zinazotumika, zikitumika kupitia `{{ icon('jina') }}` (Jinja) au
  `iconSvg('jina')` (JS, kwenye `browse.html`/`base.html`). Ukihitaji icon
  mpya isiyo kwenye sprite, ongeza kwenye sprite hiyo (ina `<symbol id="icon-jina">`).
- **Google Fonts imeondolewa** -> font ya default ya simu (system font).
- **Eneo (area)** sasa ni dropdown funge (`utils/constants.py` -> `AREAS`),
  si maandishi huru -- rahisisha utafutaji sahihi. Kuongeza eneo jipya,
  hariri orodha hiyo.
- **Umbali** sasa unapimwa kwa **dakika** (si km) -- safu ya database
  (`distance_to_college`) haikubadilika, ni namba tu, tafsiri yake tu
  imebadilika.
- **Picha za Cloudinary** sasa zinapata transformation (`w_400/w_1000/w_150,
  q_auto,f_auto`) kabla ya kuonyeshwa -- angalia `utils/cloudinary_utils.py`.
- **Hatua za maombi** (`connected` na `payment_in_progress`) zimeunganishwa
  kuwa moja -- flow sasa ni `pending -> connected -> booked/cancelled`.
- Maswali ya admin kwa kila mstari (`get_user_by_id` N+1) yamebadilishwa
  kuwa ombi moja la `list_users` (`utils/auth_utils.get_users_map`).

## 13. Sasisho la Mwisho (kabla ya uzinduzi)

**MUHIMU -- fanya hili kwanza:** database yako ya Supabase iliyopo tayari
(live) haina safu mpya zilizoongezwa hivi karibuni, hivyo utaona error kama
"Could not find the 'verification_status' column..." mpaka uendeshe
MIGRATION iliyoko chini ya `supabase_schema.sql` (Supabase → SQL Editor →
bandika sehemu ya "MIGRATION KWA DATABASE ILIYOPO" → Run). Baada ya hapo,
deploy tena code hii (Vercel), na error itaisha kabisa.

Mabadiliko ya mwisho:

- **Uthibitishaji wa vyumba (verification_status) umeondolewa kabisa** --
  ndicho kilichokuwa kinasababisha error kwenye picha uliyotuma. Chumba
  sasa kinaonekana moja kwa moja kikiwekwa, hakuna hatua ya ziada ya
  "Thibitisha/Kataa".
- **Admin sasa anaweza kuweka chumba kwa niaba ya mwenye nyumba** (kwa
  wale wasio na akaunti au simu janja) kupitia `/rooms/new` (link "Weka
  Chumba (kwa Mwenye Nyumba)" kwenye menu ya admin). Fomu inaongeza sehemu
  ya jina la mwenye nyumba; namba yake ya simu inatumia sehemu ile ile ya
  "namba ya simu" iliyokuwepo tayari. Chumba hicho hakina `owner_id`
  (hakuna akaunti), lakini kina `owner_name` na `contact_phone` moja kwa
  moja, hivyo kinaonekana sawa kabisa kwa wateja.
- **Admin anapoona ombi (`/admin/requests`), sasa anaona kila kitu pamoja**:
  taarifa kamili za chumba (bei, aina, umbali), jina na simu ya
  **aliyeomba (mteja)**, NA jina na simu ya **mwenye nyumba** -- yote
  kwenye kadi moja, bila kuhitaji kutafuta kwingine.
- Msimbo wa `main_routes.py` uliokuwa unashughulikia "migration isiyokamilika"
  (query mbili tofauti kwa ajili ya verification_status/amenities)
  umeondolewa -- haukuhitajika tena baada ya uthibitishaji kuondolewa.

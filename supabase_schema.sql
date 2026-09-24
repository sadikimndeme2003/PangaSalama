-- Endesha hii kwenye Supabase SQL Editor mara moja tu, mwanzoni (database mpya).
-- Kama tayari una database iliyopo, ruka chini kabisa mpaka sehemu ya
-- "MIGRATION KWA DATABASE ILIYOPO" na uendeshe hiyo peke yake.
--
-- HATUNA table ya "users" hapa kwa makusudi: watumiaji wote (owner, client,
-- admin) wanahifadhiwa na Supabase Auth mwenyewe kwenye auth.users.
-- Jina, namba ya simu, na role (owner/client/admin) vinahifadhiwa kwenye
-- user_metadata ya kila mtumiaji (tazama routes/auth_routes.py), si kwenye
-- jedwali letu. Admin wa kwanza anatengenezwa moja kwa moja kwenye Supabase
-- Dashboard (Authentication > Users > Add user), kisha ongeza
-- {"role": "admin", "full_name": "..."} kwenye user_metadata yake.

create extension if not exists "pgcrypto";

-- Vyumba vilivyowekwa na wamiliki (au na admin kwa niaba ya mwenye nyumba
-- asiye na akaunti/simu janja -- angalia owner_id/owner_name chini)
create table if not exists rooms (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid references auth.users(id) on delete cascade,
        -- NULL ikiwa admin ndiye aliyeweka chumba kwa niaba ya mwenye
        -- nyumba asiye na akaunti kwenye mfumo (angalia owner_name chini)
    owner_name text,            -- jina la mwenye nyumba (kwa maonyesho tu,
                                 -- hasa muhimu pale owner_id ni NULL)
    title text not null,
    area text not null,                 -- eneo (dropdown funge -- tazama utils/constants.py -> AREAS)
    distance_to_college numeric,        -- umbali KWA DAKIKA kutoka chumba hadi chuo
    price numeric not null,
    room_type text not null,            -- mfano: single, shared, self-contained
    features text,                      -- maelezo mengine ya ziada (nje ya amenities)
    amenities text[] not null default '{}',  -- mfano: {maji,umeme,choo_ndani}
    extra_directions text,              -- maelekezo ya ziada ya kufika
    contact_phone text not null,        -- namba ya simu ya mwenye nyumba
    status text not null default 'available'
        check (status in ('available', 'requested', 'pending_payment', 'booked', 'archived')),
    views integer not null default 0,   -- idadi ya watu walioangalia ukurasa wa chumba
    created_at timestamptz default now()
);

-- Picha/video za kila chumba (Cloudinary URLs)
create table if not exists room_media (
    id uuid primary key default gen_random_uuid(),
    room_id uuid references rooms(id) on delete cascade,
    url text not null,
    media_type text not null check (media_type in ('image', 'video')),
    public_id text not null,            -- Cloudinary public_id, kwa ajili ya kufuta baadaye
    created_at timestamptz default now()
);

-- Maombi: yanaweza kuwa request ya chumba fulani, au custom request (chumba hakipo)
create table if not exists requests (
    id uuid primary key default gen_random_uuid(),
    request_type text not null check (request_type in ('room_request', 'custom_request')),
    room_id uuid references rooms(id) on delete set null,
    client_id uuid references auth.users(id) on delete cascade,
    owner_id uuid references auth.users(id) on delete set null,
    desired_area text,
    desired_distance numeric,           -- KWA DAKIKA
    desired_room_type text,
    desired_price numeric,
    notes text,
    status text not null default 'pending'
        check (status in ('pending', 'connected', 'booked', 'cancelled')),
        -- 'connected' inajumuisha "malipo yanaendelea" pia (hatua moja tu,
        -- si mbili tofauti -- inapunguza click za admin)
    admin_notes text,
    created_at timestamptz default now()
);

create index if not exists idx_rooms_status on rooms(status);
create index if not exists idx_requests_status on requests(status);

-- Arifa (notifications) kwa watumiaji wote (client/owner/admin)
create table if not exists notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade,
    message text not null,
    link text,                          -- path ya ndani, mfano /rooms/mine
    is_read boolean not null default false,
    created_at timestamptz default now()
);

create index if not exists idx_notifications_user on notifications(user_id, is_read);

-- ============================================================
-- ROW LEVEL SECURITY: tunaiwasha kwa majedwali yote ili Supabase isionyeshe
-- onyo la "Unrestricted". Hatuongezi "policy" yoyote kwa makusudi -- server
-- yetu ya Flask ndiyo pekee inayoongea na Supabase (kwa service_role key,
-- ambayo INAPITA RLS kila wakati bila kujali policy), na browser haipati
-- funguo yoyote ya Supabase. Kuwasha RLS bila policy kunamaanisha: "anon"
-- na "authenticated" roles (ambazo hatuzitumii kabisa) hazipati NDANI YA
-- database hata kidogo -- ni salama 100% na haiathiri app yetu.
alter table rooms enable row level security;
alter table room_media enable row level security;
alter table requests enable row level security;
alter table notifications enable row level security;

-- ============================================================
-- MIGRATION KWA DATABASE ILIYOPO: kama tayari una database (rooms table
-- ipo tayari kabla ya haya), endesha MISTARI HII PEKE YAKE kwenye SQL
-- Editor (usifanye tena "create table" nzima hapo juu -- majedwali
-- yapo tayari, hii inaongeza/inasafisha tu safu zilizobadilika):
--
--   -- Ondoa uthibitishaji (verification_status) -- kipengele kimeondolewa
--   -- kabisa kwenye mfumo (kilikuwa kikisababisha error "Could not find
--   -- the verification_status column" kama database haikuwa imesasishwa
--   -- sanjari na msimbo). Chumba sasa kinaonekana moja kwa moja
--   -- kikiwekwa -- hakuna hatua ya ziada ya "Thibitisha/Kataa".
--   alter table rooms drop column if exists verification_status;
--
--   -- Ongeza jina la mwenye nyumba (kwa vyumba admin anavyoweka kwa
--   -- niaba ya mwenye nyumba asiye na akaunti/simu janja)
--   alter table rooms add column if not exists owner_name text;
--
--   -- Safu nyingine za awali (kama bado hazipo):
--   alter table rooms add column if not exists amenities text[] not null default '{}';
--   alter table rooms add column if not exists views integer not null default 0;
--
--   -- Sasisha check constraint ya requests.status (payment_in_progress
--   -- imeunganishwa na connected -- hatua moja badala ya mbili):
--   alter table requests drop constraint if exists requests_status_check;
--   alter table requests add constraint requests_status_check
--       check (status in ('pending', 'connected', 'booked', 'cancelled'));
--
--   -- Kipengele cha "vipendwa/favorites" kimeondolewa kwenye app kabisa.
--   -- Jedwali la favorites (kama lipo tayari kwenye database yako) halitumiki
--   -- tena na halina madhara likibaki -- unaweza kuliacha, au kuliondoa
--   -- kabisa kwa: drop table if exists favorites;
--
--   create table if not exists notifications (
--       id uuid primary key default gen_random_uuid(),
--       user_id uuid references auth.users(id) on delete cascade,
--       message text not null,
--       link text,
--       is_read boolean not null default false,
--       created_at timestamptz default now()
--   );
--   create index if not exists idx_notifications_user on notifications(user_id, is_read);
--
--   alter table rooms enable row level security;
--   alter table room_media enable row level security;
--   alter table requests enable row level security;
--   alter table notifications enable row level security;
--
-- ============================================================

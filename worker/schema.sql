-- D1 database "blokvolt" (binding DB in the Pages project). Paste into the D1 console to create or update.
-- Drivers' check-ins at public chargers: status, optional rating 1-5, optional short comment.
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  st TEXT NOT NULL,              -- station id from /assets/map/punjaci.json
  s TEXT NOT NULL,               -- ok | problem | broken | missing
  r INTEGER,                     -- rating 1..5 or NULL
  c TEXT,                        -- comment (<= 500 chars) or NULL
  n TEXT,                        -- nickname (<= 40 chars) or NULL
  cs TEXT NOT NULL DEFAULT 'none', -- comment state: none | ok | pending | hidden
  at INTEGER NOT NULL,           -- unix seconds
  lang TEXT,
  ip TEXT,                       -- HMAC of the IP with the day's random key (table dk); unlinkable across days
  rep INTEGER NOT NULL DEFAULT 0, -- abuse reports
  uid TEXT                       -- users.id when the driver was signed in, else NULL (the worker adds the column + index)
);
CREATE INDEX IF NOT EXISTS checkins_st ON checkins (st, at);
CREATE INDEX IF NOT EXISTS checkins_cs ON checkins (cs);

-- Photos of chargers, published only after moderation.
CREATE TABLE IF NOT EXISTS photos (
  id TEXT PRIMARY KEY,           -- 32 hex chars, random
  st TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | ok | no
  at INTEGER NOT NULL,
  cap TEXT,
  w INTEGER, h INTEGER,
  mime TEXT NOT NULL,
  img BLOB NOT NULL,             -- max ~900 KB, re-encoded in the browser (no EXIF)
  th BLOB,                       -- thumbnail max ~80 KB
  ip TEXT,
  rep INTEGER NOT NULL DEFAULT 0,
  uid TEXT                       -- users.id when the driver was signed in, else NULL (the worker adds the column + index)
);
CREATE INDEX IF NOT EXISTS photos_st ON photos (st, status);
CREATE INDEX IF NOT EXISTS photos_status ON photos (status);

-- Requests from companies and networks ("Da li je ovo vaša firma?") and corrections from readers.
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,            -- firma | mreza | ispravka | stanica
  slug TEXT,
  data TEXT NOT NULL,            -- JSON of the form
  email TEXT,
  at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'new', -- new | done | rejected
  ip TEXT
);
CREATE INDEX IF NOT EXISTS requests_status ON requests (status);

-- The day's random key for the IP fingerprints: one row, overwritten with a new random key on the first request of each
-- UTC day, so yesterday's fingerprints can no longer be matched to an address. The worker also creates it on first use.
CREATE TABLE IF NOT EXISTS dk (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  day TEXT NOT NULL,             -- YYYY-MM-DD (UTC)
  k TEXT NOT NULL                -- 64 random hex chars
);

-- Rate limits per key per day (also one report per item and visitor per day: keys rx:<c|f>:<id>:<fingerprint>).
CREATE TABLE IF NOT EXISTS rl (
  k TEXT NOT NULL,
  day TEXT NOT NULL,
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (k, day)
);

-- ---------------------------------------------------------------- accounts and the newsletter (RUNBOOK 3.27)
-- The worker creates every table below itself on first use (CREATE TABLE IF NOT EXISTS, once per isolate) and adds the
-- uid columns of checkins and photos (ALTER TABLE in try/catch), so nobody has to run this by hand. Documentation only.

-- Accounts ("Moj BlokVolt"). Sign-in by a code sent to the address; no passwords.
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,           -- 32 random hex chars
  email TEXT UNIQUE NOT NULL,    -- trimmed, lower case
  lang TEXT,                     -- sr | en | ru (language of the last sign-in or the setting)
  created_at INTEGER,
  verified_at INTEGER,           -- first successful sign-in (the code proved the address)
  last_login_at INTEGER,
  car TEXT,                      -- "Brand Model" (<= 80 chars) or NULL
  dc TEXT,                       -- ccs2 | chademo | none | NULL
  tesla INTEGER DEFAULT 0,       -- "Imam Teslu" on the map
  city TEXT                      -- slug from content/data/gradovi.json, 'drugo' or NULL
);

-- Pending sign-ins: one per address and browser (the code is checked only in the browser that asked; the link works
-- anywhere): the six-digit code and the one-click link, both as SHA-256 only, valid 15 minutes.
CREATE TABLE IF NOT EXISTS auth_codes (
  email TEXT NOT NULL,
  nonce TEXT NOT NULL,           -- the browser that asked (HttpOnly cookie bv_n) or the app's nonce: one code each
  code_hash TEXT,                -- sha256(salt + code)
  link_hash TEXT,                -- sha256(link token)
  salt TEXT,
  exp INTEGER,
  tries INTEGER DEFAULT 0,       -- 5 attempts, then the code is deleted
  at INTEGER,
  lang TEXT,
  opt_in INTEGER DEFAULT 0,      -- "Pošaljite mi i Nedeljni pregled" ticked at sign-in
  PRIMARY KEY (email, nonce)
);
CREATE INDEX IF NOT EXISTS auth_codes_link ON auth_codes (link_hash);

-- Sessions: the token is in the HttpOnly cookie bv_s (web) or the app's Authorization header; only its hash is here.
CREATE TABLE IF NOT EXISTS sessions (
  h TEXT PRIMARY KEY,            -- sha256 hex of the token
  uid TEXT NOT NULL,
  at INTEGER,
  seen INTEGER,                  -- updated at most once an hour
  exp INTEGER,                   -- seen + 90 days
  kind TEXT                      -- web | app
);
CREATE INDEX IF NOT EXISTS sessions_uid ON sessions (uid);

-- Favourite chargers of an account (at most 300, ids that exist on /mapa/).
CREATE TABLE IF NOT EXISTS favs (
  uid TEXT NOT NULL,
  st TEXT NOT NULL,
  at INTEGER,
  PRIMARY KEY (uid, st)
);

-- Newsletter (Nedeljni pregled): one row per address, with or without an account.
CREATE TABLE IF NOT EXISTS subs (
  email TEXT PRIMARY KEY,
  uid TEXT,
  lang TEXT,
  topics TEXT,                   -- comma list of vesti,cene,punjaci,moji
  freq TEXT,                     -- w | m
  status TEXT,                   -- pending | on | off
  token TEXT UNIQUE,             -- 32 random hex: links to confirm, unsubscribe and change the settings
  src TEXT,                      -- where the sign-up came from (page path, nalog, nalog-prijava)
  consent_v TEXT,                -- version of the consent text (pregled-v1)
  created_at INTEGER,            -- start of the current sign-up; pending rows are deleted 30 days after it
  confirmed_at INTEGER,
  off_at INTEGER,
  off_reason TEXT                -- link | nalog | bounce | complaint
);
CREATE INDEX IF NOT EXISTS subs_status ON subs (status, created_at);

-- Consent log (append-only; ZZPL art. 15). granted 1 = consent, 0 = withdrawal (or an unconfirmed sign-up that expired,
-- a hard bounce, a spam complaint). After an account is deleted, and when an unconfirmed sign-up expires (30 days), email
-- holds 'sha256:' + the hash of the address. Deleted 3 years after the last withdrawal.
CREATE TABLE IF NOT EXISTS consents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT,
  kind TEXT,                     -- pregled
  granted INTEGER,
  text_v TEXT,
  src TEXT,                      -- page path | confirm-click | nalog | nalog-prijava | one-click | odjava | brisanje-naloga |
                                 -- isteklo | bounce | complaint
  at INTEGER,
  ip TEXT                        -- the day's IP fingerprint, as in checkins
);
CREATE INDEX IF NOT EXISTS consents_email ON consents (email);

-- Addresses that are not mailed again: a hard bounce or a spam complaint reported by Resend's webhook
-- (POST /api/posta/resend). Only the SHA-256 (hex) of the address; every send checks it first.
CREATE TABLE IF NOT EXISTS suppressions (
  email_hash TEXT PRIMARY KEY,
  reason TEXT,                   -- bounce | complaint
  at INTEGER
);

-- Only with MAIL_MODE=log (local tests): outgoing mail is stored here instead of being sent.
CREATE TABLE IF NOT EXISTS mail_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at INTEGER,
  to_addr TEXT,
  subject TEXT,
  html TEXT,
  text TEXT,
  kind TEXT,                     -- code | confirm | welcome
  hdr TEXT                       -- JSON: List-Unsubscribe headers and the Idempotency-Key
);

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
  city TEXT,                     -- slug from content/data/gradovi.json, 'drugo' or NULL
  valuta TEXT                    -- display currency RSD | EUR | USD, NULL = never chosen (RUNBOOK 3.29; the worker adds the column)
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
  kind TEXT,                     -- code | confirm | welcome | preview | pregled | notice
  hdr TEXT                       -- JSON: List-Unsubscribe headers and the Idempotency-Key
);

-- ---------------------------------------------------------------- sending the issues (RUNBOOK 3.27, "Sending the issues")
-- POST /api/posta/tick reads /pregled-mail/index.json and /pregled-mail/<slug>.json (written by build.py) and uses the
-- tables below; the worker creates them on first use like the ones above. Documentation only.

-- The previews sent to the team address: one row per issue and content hash. An issue is sent only when its
-- approved_hash is one of these hashes and still the hash of its file.
CREATE TABLE IF NOT EXISTS pg_previews (
  slug TEXT NOT NULL,
  hash TEXT NOT NULL,            -- sha256 of the issue's content (langs + links), from the file
  at INTEGER,                    -- when the three previews (sr, en, ru) went out
  PRIMARY KEY (slug, hash)
);

-- One row per issue once it was queued (an issue is queued once), or stopped from /api/admin/posta.
CREATE TABLE IF NOT EXISTS pg_issues (
  slug TEXT PRIMARY KEY,
  hash TEXT,                     -- the hash it was queued with
  enqueued_at INTEGER,
  queued INTEGER,                -- rows made at that moment
  stopped_at INTEGER             -- POST /api/admin/posta {"stop": slug}: never queued or sent again
);

-- The send queue: one row per issue and reader. The mail is made when the row is sent, in the reader's language and
-- topics of that moment; a reader who is no longer on, whose topics no longer match or whose address was suppressed is
-- 'cancelled'. The address is removed (NULL) 60 days after the row was sent or given up, and at once when the account
-- is deleted.
CREATE TABLE IF NOT EXISTS pg_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL,
  email TEXT,
  lang TEXT,                     -- sr | en | ru (at the enqueue; the language actually sent once it is sent)
  topics TEXT,                   -- the reader's topics at the enqueue
  month TEXT,                    -- YYYY-MM of the issue's date: a monthly reader gets one issue a calendar month
  status TEXT NOT NULL,          -- queued | sent | failed | cancelled
  attempts INTEGER NOT NULL DEFAULT 0,  -- a 429, a 5xx or a timeout from Resend: +1; failed at 5
  provider_id TEXT,              -- Resend's id of the sent mail
  at INTEGER,                    -- queued at
  sent_at INTEGER,               -- counts against PREGLED_DAILY_CAP (newsletter mails per UTC day, default 30)
  note TEXT,                     -- why cancelled or failed: off | suppressed | topics | stopped | admin | obrisan | resend <status>
  UNIQUE (slug, email)
);
CREATE INDEX IF NOT EXISTS pg_queue_status ON pg_queue (status, id);
CREATE INDEX IF NOT EXISTS pg_queue_sent ON pg_queue (sent_at);
CREATE INDEX IF NOT EXISTS pg_queue_email ON pg_queue (email, month);

-- Clicks on the links of the issues (GET /api/posta/klik?i=<slug>&l=<n>): counts per issue, link and day, nothing
-- about the reader.
CREATE TABLE IF NOT EXISTS pg_clicks (
  slug TEXT NOT NULL,
  l INTEGER NOT NULL,            -- the number in the issue's link table (links in its file)
  day TEXT NOT NULL,             -- YYYY-MM-DD (UTC)
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (slug, l, day)
);

-- One row: at most one tick at a time and one a minute (the background tick of normal requests: one every 10 minutes).
CREATE TABLE IF NOT EXISTS pg_lock (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  at INTEGER NOT NULL DEFAULT 0, -- when the last tick started (unix seconds)
  until INTEGER NOT NULL DEFAULT 0  -- while a tick runs: at + 600 (a tick that died frees the lock then); 0 when done
);

-- Drivers' short answers on the map card (the worker also creates it on first use): what went wrong with a report
-- (why: busy | broken | app | cable | closed | short), cable (cab: att | own), parking (park: free | paid), hours (oh: 24 | lim).
CREATE TABLE IF NOT EXISTS facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  st TEXT NOT NULL,
  f TEXT NOT NULL,
  v TEXT NOT NULL,
  at INTEGER NOT NULL,
  ip TEXT,                       -- day fingerprint, as in checkins
  uid TEXT
);
CREATE INDEX IF NOT EXISTS facts_st ON facts (st, at);

-- Hits on the hidden link of /mapa/ (/api/zamka, forbidden in robots.txt): only counted, never blocked. The worker creates it.
CREATE TABLE IF NOT EXISTS trap (day TEXT NOT NULL, fp TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, ua TEXT, PRIMARY KEY (day, fp));

-- ---------------------------------------------------------------- display currency (RUNBOOK 3.29)
-- The last good NBS middle rate behind GET /api/kurs: one row, overwritten after every successful fetch from
-- kurs.resenje.org. Served with stale:true while the source does not answer. The worker creates it on first use.
CREATE TABLE IF NOT EXISTS kurs (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  date TEXT NOT NULL,            -- YYYY-MM-DD of the NBS exchange list
  eur REAL NOT NULL,             -- RSD for 1 EUR (exchange_middle ÷ parity), 100–140
  usd REAL NOT NULL,             -- RSD for 1 USD, 80–140
  fetched_at TEXT NOT NULL       -- ISO time of the fetch (UTC)
);

# Al Noir — Jurnal sesiune (5-6 august 2026)

Acest fișier documentează tot ce s-a făcut într-o singură sesiune de lucru cu Claude Code, de la un proiect Django local netestat până la un site live, funcțional, deployat pe Render.

## Stare finală

- **Live la:** https://al-noir.onrender.com
- **Admin:** https://al-noir.onrender.com/admin/ (user `AlNoir`)
- **Bază de date:** Neon Postgres (`DATABASE_URL`)
- **Media/imagini:** Cloudinary
- **Plăți:** Stripe (mod test), monedă **USD**
- **Limbă:** doar engleză (fără selector de limbă)

---

## 1. Bug-uri reale găsite și reparate (13 total)

Audit sistematic pe tot codul (nu doar citire — fiecare fix a fost testat funcțional local înainte de commit).

**Din primul pas (reservations/operations):**
1. Webhook Stripe crăpa mereu — `Reservation` folosit fără import (`NameError`)
2. Dublă rezervare a aceleiași mese — fără blocaj; adăugat `UniqueConstraint` la nivel de DB
3. Cod promo folosit de mai multe ori decât `max_uses` — race condition; reparat cu `select_for_update()`
4. `guests=0` la rezervare dădea crash (`AttributeError`) — verificare falsy greșită
5. Fără control-acces pe checkout Stripe — oricine cu un `pk` ghicit putea declanșa plata altcuiva; adăugat `access_token` unic per rezervare

**Din al doilea pas (audit complet):**
6. `LoyaltyTransaction` folosit fără import în `redeem_reward` — același tip de bug ca #1, crăpa la fiecare răscumpărare de recompensă
7. Sistemul de mesaje Django (`messages.success/error`) nu era afișat nicăieri în afară de o singură pagină — adăugat bloc global în `base.html`
8. Contact/review formulare dădeau JSON brut dacă JS nu rula (fără fallback non-AJAX)
9. `reports()` financiar crăpa la parametri de dată invalizi în URL
10. Interogarea `top_items` din `reports()` crăpa **mereu** — alias `quantity=Sum('quantity')` suprapunea numele câmpului real, cauzând "agregare peste agregare"
11. `Event.capacity` nu era verificat niciodată — evenimente puteau fi suprarezervate nelimitat
12. Race condition la acumularea punctelor de fidelitate (`LoyaltyAccount.add_points`) — pierdere silențioasă la vânzări simultane
13. `TicketForm`/`WaitlistForm` acceptau `quantity=0`/`guests=0`

**Bug găsit ulterior (verificare vizuală):**
- Meniul afișa prețuri cu `$` hardcodat inconsistent cu restul site-ului (care folosea "lei") — rezolvat prin trecerea **întregului site** la USD (vezi secțiunea 6)

## 2. Deploy pe Render (de la zero la live)

- **Bază de date:** SQLite local → Neon Postgres prin `DATABASE_URL` (`dj-database-url`, `psycopg`)
- **Static files:** WhiteNoise + `STATIC_ROOT`; reparat conflict între `STORAGES` (Django 4.2+) și `django-cloudinary-storage` (înțelege doar `STATICFILES_STORAGE` vechi) — trebuiau setate ambele în paralel
- **Flag `--upload-unhashed-files`** necesar în build command, altfel `django-cloudinary-storage` sare peste copierea fișierelor statice neCloudinary
- **Media:** Cloudinary (cont gratuit, cheile în variabile de mediu)
- **Secrete:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` mutate din cod în variabile de mediu (`.env` local, Render dashboard live)
- **Python 3.14 vs 3.13:** Render folosea implicit 3.14, iar `psycopg-binary==3.2.3` nu avea build pentru el — fixat prin `PYTHON_VERSION=3.13.4` + upgrade la `psycopg==3.2.10`
- **Superuser fără Shell:** cont Render gratuit nu are acces la Shell; creat `core/management/commands/ensure_superuser.py`, idempotent, rulează la fiecare deploy din `DJANGO_SUPERUSER_*` env vars
- **CSRF/SSL:** `SECURE_PROXY_SSL_HEADER` + `CSRF_TRUSTED_ORIGINS` pentru proxy-ul Render
- **`render.yaml`** creat pentru reproductibilitate (nu a fost folosit direct — serviciul a fost creat manual din dashboard din cauza cerinței de card la Blueprint)
- Serviciul rulează pe planul **Free** ($0/lună) în workspace-ul existent al userului, proiect "Entertainment_tech"

## 3. Funcționalitate nouă: scădere automată a stocului

`MenuItem` are acum un câmp opțional `stock_item` (FK către `operations.StockItem`). Când se creează o `Sale` fără `stock_item` explicit, îl preia automat de la produsul de meniu vândut, iar `StockMovement` se creează automat — stocul scade singur, fără ca staff-ul să aleagă manual de fiecare dată.

## 4. Conținut populat (date fictive, restaurant de test)

- **Site Settings:** nume, slogan, descriere, adresă (12 Victoriei Street, Bucharest), telefon, email, program
- **Meniu:** 4 categorii (Starters, Main Courses, Grills, Desserts), 8 produse cu descrieri și prețuri; Baklava marcată drept recompensă de loialitate
- **Mese:** 6 mese, capacități 2-10 persoane
- **Cont admin:** `AlNoir`, creat automat la deploy

## 5. Îmbunătățiri UX admin

- Link direct în `/admin/` către **Staff Dashboard** și **Financial Reports** (nu mai trebuie tastat URL-ul manual)
- Raportul financiar filtrat pe perioadă includea doar vânzările de meniu, omițea bilete și avansuri din acel interval — reparat să adune toate cele 3 surse
- Cheltuielile defalcate pe categorii (Supplier / Salary / Other) atât în dashboard cât și în raport
- Produse expirate evidențiate roșu în dashboard, la fel ca stocul sub prag

## 6. Traducere completă RO → EN + eliminare selector de limbă

- Eliminat `LocaleMiddleware`, context processor `i18n`, ruta `/i18n/set-language/`, dropdown-ul RO/EN din navbar
- `LANGUAGE_CODE` schimbat la `en-us`
- Tradus tot textul rămas în română: template-uri (terms, privacy, dashboard-uri, formulare), mesaje din view-uri, erori de validare, `choices` din modele (roluri staff, categorii cheltuieli, tipuri mișcări stoc, statusuri waitlist)
- **Monedă schimbată din RON/lei în USD** peste tot: meniu, checkout Stripe, facturi PDF, dashboard financiar, rapoarte, JS de calcul avans rezervare
- `core/utils.py` (`transliterate_ro`) păstrat neschimbat — protejează facturile PDF de caractere garble dacă numele clienților au diacritice, independent de limba interfeței

## Note pentru sesiuni viitoare

- **Venv-ul local** a fost recreat cu Python 3.13 (cel vechi referea un Python 3.11 care nu mai exista pe disc)
- **Toate commit-urile** au fost testate local (`manage.py check` + `manage.py test` + verificări funcționale directe prin shell) înainte de push — niciun fix nu a fost "doar teoretic"
- **Auto-deploy activat** pe Render — orice push pe `main` declanșează deploy automat
- Rămâne opțional de configurat: `STRIPE_WEBHOOK_SECRET` (sărit intenționat, poate fi adăugat oricând din dashboard Stripe folosind URL-ul live)

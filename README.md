# Al Noir — A Restaurant Website Built by Andreea Tech

**Live demo:** https://al-noir.onrender.com
*(free hosting — the site can take 30–50 seconds to wake up on the first visit after a while of no traffic)*

Everything on the site — the menu, the reviews, the contact details — is fictional. It's a demo, built to show what's possible, not a real restaurant.

## Screenshots

| | |
|---|---|
| ![Home page](docs/screenshots/home.png) | ![Menu page](docs/screenshots/menu.png) |
| ![Reservation form](docs/screenshots/reservations.png) | ![Events page](docs/screenshots/events.png) |

<details>
<summary>More screenshots</summary>

![About page](docs/screenshots/about.png)

</details>

---

## What is this?

Al Noir is a demo restaurant website that does everything a real restaurant needs online: guests can browse the menu, book a table, pay a deposit securely by card, join a waitlist when it's full, and buy tickets to events. Guests who create an account can track their reservations and earn loyalty rewards. Behind the scenes, staff get a dashboard to track stock, sales, and finances — without touching a spreadsheet.

It's built to be a working example of what a custom website can actually do for a business — not a template with a booking form glued on top.

## Built to hold up under real use

Most demo projects get built and never really tested. This one wasn't left that way. Before it went live, it went through a full audit looking for the kind of problems that only show up once real people are using a site at the same time — not the kind you'd catch by clicking around it once yourself.

A few real examples of what that audit found and fixed:

- **Double bookings.** Two guests could book the exact same table for the exact same time slot, with nothing stopping it. Now it's technically impossible, even if two people click "Reserve" at the same second.
- **A payment page that trusted the wrong thing.** With a guessable link, someone could have triggered the payment step for *someone else's* reservation. Fixed so only the person who made a booking can pay for it.
- **Loyalty points that could silently disappear.** If two purchases happened close together, the points balance could be overwritten instead of added up correctly — so a customer's rewards would just quietly vanish. Fixed so every purchase is counted properly, no matter the timing.
- **A promo code that could be used more than allowed.** A code capped at, say, 50 uses could slip past that limit if enough people redeemed it at nearly the same moment. Fixed so the limit actually holds.
- **A financial report that crashed every single time it was opened.** A subtle bug in how the numbers were being totaled meant the report page failed on every request — until it was traced and fixed.
- **Event tickets with no real limit.** A capacity field existed on every event, but it was never actually checked — so an event could be oversold indefinitely. Fixed so ticket sales stop once an event is full.

This is the kind of thing a site needs before it handles real bookings and real payments — not after.

## What guests can do

- Browse the menu with prices and photos, save favorites, and leave ratings
- Book a table online, with an optional deposit paid securely by card
- Get a confirmation page they can bookmark — no account required
- Join a waitlist when there's no table available
- Buy tickets to events, with seat limits enforced automatically
- Create an account to track reservations and earn loyalty rewards

## What staff get

- A dashboard showing stock levels, sales, and upcoming shifts — with automatic warnings for low stock or ingredients about to expire
- Financial reports combining menu sales, ticket revenue, and reservation deposits over any date range
- Stock that updates itself automatically every time something sells — no manual counting
- Downloadable PDF invoices

## Built with

Django (a mature, security-focused framework used by companies like Instagram and Pinterest), a PostgreSQL database, and Stripe for payments — the same payment processor used by Amazon and Shopify.

*(Technical setup and architecture details, for developers, live in [DEVELOPMENT.md](DEVELOPMENT.md).)*

---

Want a site like this for your business? [See more of my work](https://andreeastech.pythonanywhere.com) or get in touch.

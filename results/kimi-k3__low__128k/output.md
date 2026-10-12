# Ledgerling — session summary

## Project & goal
Ledgerling: web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling`. Launch Nov 20 (slipped from Nov 13, pricing page not ready). Beta target: 150 users (raised from 100).

## Stack & hard rules
- Fastify (NOT Express — schema validation sold the user), Postgres, Kysely, vitest, TypeScript.
- pnpm ONLY, never npm (lockfile drift trauma).
- Dev server port 4177. Database `ledgerling_dev`.
- Node 22.6.1 everywhere (`.nvmrc`, Dockerfile bumped; replaced 20.11.3 which lost dependency support).
- Never force-push main. Secrets only in `.env.local` or host secret store, never committed.
- User is in Porto, Europe/Lisbon; reminders must fire at correct local hour.
- Don't log raw email addresses (use customer id or hash).
- Commit style: small commits, tidy history.

## Config values
- Reminder cadence: 4, 9, 18 days past due date. In `config/defaults.ts`.
- Public API rate limit: 40 req/min per token. In `config/defaults.ts`.
- Pricing in `config/plans.ts`: Solo $27/month (raised from $21 after support costing), Team $54/month, 14-day trial, no card up front.
- Auth: magic links by email, 30-min expiry. Sessions in Postgres (Redis scrapped — too much to operate; `ioredis` removed, 3 leftover comment/doc mentions were being cleaned).
- Staging: https://staging.ledgerling.example. Deploys: Thursday 07:45 UTC (changed from Tuesday — support coverage).
- Backups: nightly pg_dump 02:40 UTC to bucket `ledgerling-backups-b416`; `scripts/backup.sh` written.
- `scripts/rollback.sh` written (`./scripts/rollback.sh <tag>`). Release tagged v0.11.1, deployed to staging on Crestbox us-east-4, health ok.

## Vendors
- Hosting: Crestbox, region us-east-4.
- Payments: Coinsill.
- Email: Sendharbor (NOT Sendharbour — pricier). Ticket #7830, contact Ravi Holloway (deliverability). DKIM TXT at host `pq2._domainkey` — user added it. Daily limit raised 3,000 → 15,000. Dedicated IP question still open with their infra team. SLA 2 business days. Ticket #7380 is unrelated old-account stuff — ignore.

## Key incident (resolved)
Day 3: reminders fired wrong hour for Europe/Lisbon users. Root cause: `nextSendAt` in `src/jobs/scheduler.ts` used fixed `OFFSET_MIN` computed at boot (from first scheduler commit 0705717) instead of per-user IANA zone; broke across DST. Ruled out: `cronwright` v3.2.1 handles DST correctly (verified with node one-liner). Fix: `zonedTimeToUtc` from `src/lib/tz` per send; also fixed `Math.floor(offsetMin/60)` → `offsetMin/60` for half-hour zones. Regression test `src/jobs/scheduler.test.ts` added. Committed as 914541e ("fix: resolve user IANA zone per send in scheduler (DST)"). 17 users got mistimed reminders (noted for incident summary).

## Decisions (docs/decisions.md)
- No rewrite until after launch (Tomasz proposed one; rejected).
- Founder has final say on pricing.
- pnpm only.
- Invoice footer wording stays generic until accountant Odile Fenwick answers VAT question (user to ask this week).
- Annual plan decision deferred until after first 10 paying signups.
- Error messages: translate user-actionable ones, keep internal errors English with stable codes.

## Open items / who owes what
- IMMEDIATE task in progress: user asked (before leaving for evening) to (1) add env var table to README FIRST, then (2) add nullable `snoozed_until` column to reminders via migration. README has Environment section (line 12-14) with "TODO: list every variable here." Vars found in `src/config.ts`: PORT (default 4177), DATABASE_URL, MAIL_API_KEY, PAY_API_KEY. Migration not yet written.
- Flaky test `reminders > sends at the user's local 9am` (depends on real clock, passed on retry) — user said leave for now, look later. Agent committed to investigating separately.
- User owes: SVG logo (landing page + email header) later this week; text placeholder in use until then.
- User owes: call Tomasz Wrobel (part-time dev, "Tomasz", referred to as she/her in latest message) Friday morning — she felt excluded from Solo price change decision; user will acknowledge and offer seat in next pricing review. Agent to nudge in-session.
- Sendharbor owes: dedicated IP pricing answer (ticket #7830).
- Odile Fenwick owes: VAT-on-invoices answer.
- Backlog (`docs/backlog.md`, 'later'): CC bookkeeper on reminders — requested by Dov/Bram/Faro/Gita/Hugo (Tern Audio), Kira (Saffron Works + Oaktree Studio), Faro (Vesper Type), Elin (Northwind Print), Gita (Quill & Co), Dov/Hugo (Umber Films), Lars (Saffron Works). Low priority, not this week.

## Working state notes
- Tests: suite green (last full runs ~226 tests passing). Recurring pattern: occasional fixture failures fixed by changing `amount: 0` to a nonzero value in the relevant test file.
- Lint: only unused-variable warnings, no errors; cleanup planned as separate commit.
- Many migrations applied (e.g. 0020-0080 range adding label/notes/source/external_ref/retry_after columns to various tables).
- `docs/dns.md` holds the DKIM record.
- Env table in README is the next concrete action, then the `snoozed_until` migration.
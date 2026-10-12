# Ledgerling — Session Summary

## Project & Goal
Ledgerling: small web app that nags clients about overdue invoices on behalf of freelancers. User is in Porto (Europe/Lisbon) — timezone correctness matters. Repo: `~/code/ledgerling` (git initialized).

## Current Targets (latest values)
- Launch: **Nov 20** (slipped from Nov 13 — pricing page wasn't ready).
- Beta goal: **150 users** (raised from 100).

## Stack & Environment (decided)
- TypeScript, Fastify (NOT Express — schema validation won), Postgres, Kysely, zod. Tests: vitest. Dev runner: tsx.
- **pnpm only, never npm** (lockfile drift).
- Dev port **4177**. Database: `ledgerling_dev`.
- Node: **22.6.1** everywhere (`.nvmrc`, Dockerfile) — bumped from 20.11.3 because a dependency required it.
- Base deps installed: fastify 4.28.1, kysely 0.27.4, pg 8.12.0, typescript 5.5.4, vitest 1.6.0, tsx 4.16.2. Many later `pnpm add`s: pretty-bytes, dotenv, ms, ajv, undici, nanoid, date-fns, superjson, pino. `ioredis` removed.

## Auth & Sessions
- No passwords. Magic links by email, **30-minute expiry**.
- Sessions in **Postgres** (sessions table + expiry index + cleanup job). Redis was scrapped ("too much to operate for this scale"); 3 leftover Redis mentions in comments/docs were being cleaned.

## Product Config
- Reminder cadence: **4, 9, 18 days** past due. API rate limit: **40 req/min per token**. Both in `config/defaults.ts`.
- Pricing (`config/plans.ts` + pricing page copy): Solo **$27/month** (raised from $21 — support costs), Team **$54/month**, 14-day trial, no card up front.
- Annual plan: decision deferred until after first 10 paying signups; don't spend time now.
- Invoice footer wording stays **generic** until accountant answers VAT question.

## Vendors
- Hosting: **Crestbox**, region **us-east-4**. Payments: **Coinsill**. Email: **Sendharbor** (not Sendharbour).
- Staging: `https://staging.ledgerling.example` — deployed, tag **v0.11.1**, health ok. Rollback: `./scripts/rollback.sh <tag>`. Tags: v0.1.0, v0.2.0, v0.11.1.
- Production deploys: **Thursday 07:45 UTC** (changed from Tuesday — support coverage).
- Backups: nightly `pg_dump` at **02:40 UTC** to bucket **ledgerling-backups-b416**; `scripts/backup.sh` written.

## Sendharbor Support
- Ticket **#7830**, contact **Ravi Holloway** (deliverability). Limit raised 3,000 → **15,000 emails/day**. DKIM TXT at host `pq2._domainkey` — user added it. **Dedicated IP question still open** with their infra team; Ravi to reply (SLA 2 business days). Ticket #7380 is unrelated — ignore.

## Standing Rules (user-stated)
- pnpm only; never force-push main; secrets only in `.env.local` or host secret store, never committed.
- No rewrite until after launch (Tomasz proposed one; deferred). Founder has final say on pricing. Both in `docs/decisions.md`.

## People
- **Tomasz Wrobel** (part-time dev): felt excluded from the Solo price change. User will **call her Friday morning** to acknowledge and offer a seat in the next pricing review — agent promised to remind user in-session.
- **Odile Fenwick** (accountant): user to ask this week whether VAT must appear on invoices.
- Logo: **user owes an SVG** (landing page + email header) later this week; text placeholder (app name) in use until then.

## DST Bug (fixed)
- Symptom: Europe/Lisbon tester got reminders an hour off after the clocks changed (17 users affected — noted for incident summary).
- Root cause: `src/jobs/scheduler.ts` `nextSendAt` used fixed `OFFSET_MIN` computed at boot (introduced in commit 0705717) instead of resolving the IANA zone per send.
- **Ruled out:** cronwright v3.2.1 — verified it handles the DST boundary correctly.
- Fix: per-send zone resolution via `src/lib/tz.ts` (`zonedTimeToUtc`), plus half-hour-zone fix (removed `Math.floor`). Regression test in `src/jobs/scheduler.test.ts`. Committed as **914541e**.
- **Known flaky test:** `reminders > sends at the user's local 9am` (passes on retry, depends on real clock). User said leave it, look later.

## Backlog (parked, low priority)
`docs/backlog.md` 'later': CC-bookkeeper-on-reminders requests from Dov/Bram/Faro/Gita/Hugo (Tern Audio), Kira/Lars (Saffron Works), Faro (Vesper Type), Gita (Quill & Co), Elin (Northwind Print), Kira (Oaktree Studio), Dov/Hugo (Umber Films). Not this week.

## Task In Progress (do next, in this order)
1. **README env var table** (user said start here). `README.md` has `## Environment` (line 12) with "Copy `.env.example` to `.env.local`." and a TODO. Vars from `src/config.ts`: `PORT` (default '4177'), `DATABASE_URL` (required), `MAIL_API_KEY` (required), `PAY_API_KEY` (required).
2. **Migration: nullable `snoozed_until` column on `reminders`.** Migrations live in `db/migrations/NNNN_name.sql`, applied with `pnpm db:migrate`.

## Repo State Notes
- `src/server.ts`: Fastify on `PORT ?? 4177`, `/healthz` ok. Routes: `/v1/invoices`, `/v1/customers`, `/v1/reminders`, `/v1/templates`, `/v1/me`, `/v1/webhooks/mail`. Logs: `logs/dev.log`.
- Migrations applied this session include: 0020, 0021, 0022, 0023, 0036, 0039, 0044, 0047, 0062, 0066, 0068, 0079, 0080 (various label/notes/source/external_ref/retry_after columns).
- Tests: `pnpm vitest run` — last full runs green (e.g., 41 files / 226 tests). Several test fixtures were fixed during the session (`amount: 0` → nonzero) in: src/lib/batch, src/lib/attachment, src/mail/token, src/api/reminder, src/api/audit, src/jobs/token, src/lib/export, src/auth/customer, src/lib/customer, src/db/reminder, src/mail/attachment (all `.test.ts`).
- Lint: `pnpm eslint src --max-warnings 100` — only unused-variable warnings; cleanup planned as a separate commit.
- `pnpm tsc --noEmit` mostly clean; occasional pre-existing TS2345 in `src/auth/export.ts` / `src/mail/token.ts`.
- Commit style: small commits, prefixes like `fix:`, `chore:`, `test:`, `refactor:`, `wip:`, `tidy:`.

## Q&A Already Answered (don't re-litigate)
- `FOR UPDATE SKIP LOCKED`: locks returned rows, skips locked ones — standard Postgres job-queue pattern.
- Boolean index: usually not alone; partial index (e.g. `WHERE sent = false`) only when the subset is small.
- `Promise.all` vs `allSettled`: use `allSettled` for reminder batches.
- Error messages: translate user-actionable ones, keep internal errors in English with stable codes.
- Don't log raw email addresses; use ids/hashes.
- Pool size default: ~(cores × 2) + 1 per instance, keep total under DB max connections.
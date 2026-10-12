# Ledgerling — Session Summary

## Project & Goal
Ledgerling: a small web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling`. User is in Tallinn (`Europe/Tallinn`). Launch target: **Nov 27** (slipped from Nov 20 — pricing page not ready). Beta goal: **45 users** (raised from 30).

## Stack & Hard Rules
- TypeScript on Node, **Fastify** (Express explicitly ruled out — Fastify schema validation), Postgres, Kysely, **vitest**.
- **pnpm only, never npm** (lockfile drift).
- Dev server port **3863**; DB name **`ledgerling_dev`**; health endpoint `/healthz`.
- Node **22.5.2** everywhere (CI, Dockerfile, `.nvmrc`) — bumped from 20.11.2, which went out of support for a dependency.
- Never force-push `main`. Secrets only in `.env.local` or the host's secret store, never committed.
- Commit style: small, focused commits with prefixes (`fix:`, `refactor:`, `tidy:`, `chore:`, `test:`, `wip:`).

## Decisions (latest values only)
- **Auth**: no passwords; magic links by email expiring after **20 minutes**. Sessions in **Postgres** — this replaced Redis, which was scrapped as too much to operate at this scale (`ioredis` removed; 3 leftover Redis mentions in comments/docs still being cleaned).
- **Reminder cadence**: 3, 7 and 14 days past the due date. **Public API rate limit: 60 req/min per token.**
- **Pricing**: Solo **$26/month** (raised from $21 — $21 too low once support was costed out), Team **$54/month**, 30-day free trial, no card up front. Lives in `config/plans.ts`.
- **Vendors**: hosting **Crestbox**, region **sa-east-1**; payments **Tillpay**; email **Sendharbor** (not Sendharbour — pricier).
- **Deploys**: **Friday 07:45 UTC** (changed from Wednesday — Wednesday is bad for support coverage).
- **Backups**: nightly `pg_dump` at **02:15 UTC** to bucket **`ledgerling-backups-c079`**.
- **No rewrite before launch** (Soren proposed rewriting in a different framework; deferred). **Founder has final say on pricing** (agreed with Soren). Recorded in `docs/decisions.md` (also notes pnpm-only).
- **Annual plan**: decide after the first **10 paying signups**; no time spent on it now.
- **Invoice footer**: keep generic until the VAT question is answered.
- **Logo**: use a text placeholder until the user sends an SVG (landing page + email header).

## Staging / Release
- Tagged **`v0.9.2`**; deployed to Crestbox sa-east-1 staging; live at **https://staging.ledgerling.example**; health ok.
- Rollback: `./scripts/rollback.sh <tag>` (e.g. `./scripts/rollback.sh v0.2.0`).
- `scripts/backup.sh` written (pg_dump | gzip | aws s3 cp to the bucket).

## DST Bug (fixed)
- Tester reported reminders arriving at the wrong hour; user in `Europe/Tallinn`.
- **Ruled out**: `tickmaster` v2.8.0 cron library — verified it handles the DST boundary correctly (`node -e` check returned 09:00 local both sides).
- **Root cause**: `src/jobs/scheduler.ts` `nextSendAt` applied a fixed `OFFSET_MIN` constant computed at boot instead of resolving the user's IANA zone per send. `OFFSET_MIN` came from commit `6ab5199` ("feat: first scheduler"), unrelated to the fix.
- **Fix**: import `zonedTimeToUtc` from `../lib/tz`; added regression test `src/jobs/scheduler.test.ts`; also fixed half-hour-zone handling in `src/lib/tz.ts` (`Math.floor(offsetMin / 60)` → `offsetMin / 60`).
- Committed as **`10ea076`** "fix: resolve user IANA zone per send in scheduler (DST)" (3 files, 41 insertions, 9 deletions).
- **25 users** received a mistimed reminder in the affected week (counted from logs) — noted for the incident summary.

## Vendors / External
- **Sendharbor** support: **Dana Kessler**, deliverability team, ticket **#6139**. DKIM TXT at host **`rs3._domainkey`**; SLA 3 business days. Daily limit raised from 2,000 to **10,000 emails/day**. Dedicated IP question escalated to their infra team — **waiting on reply**. Ticket **#6319** concerns the user's old account — **ignore it**.
- **Yaw Boateng** (accountant): user will ask this week whether VAT must be shown on invoices sent through the product. Until answered, footer stays generic.

## Open Items / Who Owes What
- **Immediate next task**: add an environment variable table to `README.md` (the `## Environment` section currently says "Copy `.env.example` to `.env.local`." and "TODO: list every variable here."). Variables found in `src/config.ts`: `PORT` (default `'3863'`), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`. **README first, then** the migration.
- **Pending migration**: add a nullable **`snoozed_until`** column to `reminders`. Not yet done.
- **Flaky test**: `reminders > sends at the user's local 9am` passed only on retry (depends on the real clock). User said leave it for now, look later.
- **Call Soren Friday morning**: acknowledge she was left out of the price change and offer her a seat in the next pricing review. User asked to be reminded; the agent cannot place the call and will nudge in-session.
- **Logo SVG** owed by the user later this week.
- **Annual plan** decision after 10 paying signups.
- **CC-bookkeeper feature requests** parked in `docs/backlog.md` under 'later' (low priority, not this week). Requesters: Ada (Vesper Type), Hugo (Umber Films), Lars (Northwind Print), Juno (Vesper Type), Elin (Northwind Print), Kira (Saffron Works), Ivo (Saffron Works), Juno (Pellucid Labs), Juno (Oaktree Studio), Cleo (Oaktree Studio), Gita (Vesper Type), Kira (Ridgeline Design), Ada (Quill & Co), Elin (Saffron Works), Dov (Quill & Co).
- **Lint cleanup**: only unused-variable warnings, no errors; agent repeatedly deferred these to a separate small commit.

## Working Patterns / Notes
- Routine commands: `pnpm vitest run`, `pnpm eslint src --max-warnings 100`, `pnpm tsc --noEmit`, `pnpm db:migrate`, `tail -n N logs/dev.log`, `curl -s localhost:3863/...`.
- API endpoints seen: `/healthz`, `/v1/invoices`, `/v1/customers`, `/v1/templates`, `/v1/reminders`, `/v1/webhooks/mail`, `/v1/me`. List responses are `{ "data": [...], "next": null }`.
- Many migrations were applied during the session (mostly placeholder columns/indexes such as `*_label`, `*_external_ref`, `*_retry_after`, `*_source`, `*_notes`); nothing depends on them yet. Note some migration numbers were reused (e.g. `0035`, `0059`).
- Recurring test-fix pattern: failures like "expected N to be M" traced to a stale default in the **test fixture** (`amount: 0`), fixed in the fixture, not the code under test.
- Dependencies added over the session include: fastify, kysely, pg, zod, ajv, pino, p-limit, undici, superjson, dotenv, pretty-bytes, nanoid, date-fns, ms, plus dev deps typescript, vitest, tsx, @types/node, @types/pg.

## Questions Answered (knowledge, not project state)
- `SELECT ... FOR UPDATE SKIP LOCKED`: locks returned rows, silently skips rows locked by other transactions — standard Postgres job-queue trick.
- `Promise.all` rejects on first rejection and discards other results; `Promise.allSettled` waits for all and returns `{status, value|reason}` — use `allSettled` for batch reminder sends.
- Logging email addresses: avoid; log a customer id or hashed form, keep raw addresses out of long-retention logs.
- Boolean column index: usually not alone (planner prefers seq scan); a partial index like `WHERE sent = false` can help when unsent rows are a small fraction.
- Leap seconds: not a concern (Unix time ignores them); DST and time-zone rule updates are the real risk.
- Idempotency keys: unique id per request so the receiver recognizes retries; store the event id with a unique constraint, insert before processing, skip on conflict.
- Error messages: translate user-actionable ones; keep internal errors in English with stable error codes.
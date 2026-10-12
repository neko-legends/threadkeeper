# Ledgerling — Session Summary

## Project & goal
- **Ledgerling**: small web app that nags clients about overdue invoices on behalf of freelancers.
- Repo: `~/code/ledgerling` (git initialised, branch `main`).
- User is in **Porto, Europe/Lisbon**; timezone correctness matters ("I'm going to be annoyed if reminders fire at the wrong hour").
- Launch target: **Nov 20** (was Nov 13 — slipped a week because the pricing page isn't ready). Beta goal: **150 users** (was 100).

## Stack & hard rules
- **Fastify** (Express explicitly ruled out — Fastify's schema validation sold the user), **Postgres**, **Kysely**, **vitest**, TypeScript.
- **pnpm only, never npm** ("I've been burned by lockfile drift").
- Dev server port **4177** (usual ports collide with other stuff on the machine).
- Database name **`ledgerling_dev`**.
- Node: was 20.11.3, **bumped to 22.6.1 everywhere** (CI, Dockerfile, `.nvmrc`) because 20.11.3 went out of support for a needed dependency.
- **Never force-push `main`.**
- **Secrets only in `.env.local` or the host's secret store, never committed.**
- Git style: small commits with prefixes `fix:`, `chore:`, `refactor:`, `test:`, `tidy:`, `wip:`.
- Migrations run with `pnpm db:migrate`; dev server with `pnpm tsx src/server.ts`; health at `/healthz`.

## Auth, sessions, cadence, limits
- **No passwords. Magic links by email, expiring after 30 minutes.**
- Sessions: **Postgres** (originally Redis — **Redis scrapped**, "too much to operate for this scale"; `ioredis` removed).
- Reminder cadence: **4, 9 and 18 days past the due date**.
- Public API rate limit: **40 req/min per token**.

## Vendors & infrastructure
- Hosting: **Crestbox**, region **us-east-4**.
- Payments: **Coinsill**.
- Email: **Sendharbor** (not Sendharbour — pricier at this volume).
- Staging: **https://staging.ledgerling.example**.
- **Deploys: Thursday 07:45 UTC** (was Tuesday — changed for support coverage).
- **Backups: nightly `pg_dump` at 02:40 UTC** to bucket **`ledgerling-backups-b416`**; `scripts/backup.sh` written.
- Rollback: `scripts/rollback.sh <tag>` (e.g. `./scripts/rollback.sh v0.2.0`).
- Staging deployed and tagged **v0.11.1**; health ok.

## Pricing
- **Solo $27/month** (was $21 — raised after costing out support; this replaced the earlier value).
- **Team $54/month**. **14-day free trial, no card up front.**
- Lives in `config/plans.ts`.
- **Founder has final say on pricing** (agreed with Tomasz).

## Sendharbor support thread
- Contact: **Ravi Holloway**, deliverability team. Ticket **#7830**.
- Daily limit: started at **3,000/day**, **raised to 15,000/day**.
- **DKIM TXT at host `pq2._domainkey`** — user added it at the registrar.
- **Dedicated IP: still open**, their infra team will come back. Cost unknown.
- SLA: 2 business days.
- Ticket **#7380** concerns the user's old account — **ignore it**.

## People & open interpersonal items
- **Tomasz Wrobel** (part-time dev, "Tomasz"): wanted a full framework rewrite before launch — **deferred until after launch**. She felt left out of the pricing decision (heard the new number from the pricing-page diff). **User will call her Friday morning** to acknowledge this and offer a seat in the next pricing review. **User asked to be reminded.**
- **Odile Fenwick** (accountant): user will ask this week whether VAT must be shown on invoices sent through the product. **Until answered, keep the invoice footer wording generic.**
- **Logo**: user still owes an SVG later this week for the landing page and email header. **Use a text placeholder until then.**

## Parked / deferred
- **CC-the-bookkeeper requests** (all parked in `docs/backlog.md` under 'later', not for this week): Dov (Tern Audio), Bram (Tern Audio), Kira (Saffron Works), Faro (Tern Audio), Kira (Oaktree Studio), Faro (Vesper Type), Gita (Quill & Co), Elin (Northwind Print), Dov (Umber Films), Gita (Tern Audio), Hugo (Umber Films), Lars (Saffron Works), Hugo (Tern Audio).
- **Annual plan**: decide **after the first 10 paying signups**; no time to be spent now.

## DST bug (fixed)
- Tester in Europe/Lisbon reported reminders at the wrong hour.
- **Root cause**: `nextSendAt` in `src/jobs/scheduler.ts` applied a fixed `OFFSET_MIN` computed at boot instead of resolving the user's IANA zone per send; sends drifted by exactly one hour for the week after the clocks changed.
- **Ruled out**: `cronwright` v3.2.1 — it handles the DST boundary correctly.
- **Fix**: `Intl`-based `zonedTimeToUtc` in `src/lib/tz.ts`; also fixed half-hour zones (`offsetMin / 60` instead of `Math.floor(offsetMin / 60)`).
- Regression test added: `src/jobs/scheduler.test.ts`.
- **Committed as `914541e`** — "fix: resolve user IANA zone per send in scheduler (DST)".
- **17 users** received a mistimed reminder in the affected week (counted from logs).
- **Known flaky test**: `reminders > sends at the user's local 9am` (depends on the real clock; passed only on retry). User said **leave it for now, look later**.

## Decisions recorded
- `docs/decisions.md` written, containing: no rewrite until after launch; founder has final say on pricing; pnpm only.

## Work in progress at cut-off
- User's final request: **add a nullable `snoozed_until` column to `reminders` via a migration**, and **add an environment variable table to the README**. **Start with the README.**
- README has a `## Environment` section (around lines 12–14) containing "Copy `.env.example` to `.env.local`." and "TODO: list every variable here." — the table is **not yet written**.
- Env vars found in `src/config.ts`: **`PORT`** (default `'4177'`), **`DATABASE_URL`**, **`MAIL_API_KEY`**, **`PAY_API_KEY`**.
- The `snoozed_until` migration is **not yet written**.

## Migrations already applied to `ledgerling_dev`
`0020_add_mail_events_label`, `0062_add_tenants_source`, `0044_add_payments_external_ref`, `0080_add_tenants_notes`, `0036_add_webhook_events_label`, `0039_add_customers_retry_after`, `0023_add_payments_notes`, `0066_add_invoices_source`, `0079_add_api_tokens_external_ref`, `0068_add_audit_log_notes`, `0047_add_api_tokens_notes`, `0021_add_customers_label`, `0022_add_payments_external_ref`. (Each adds a nullable text column plus an index; nothing depends on them yet.)

## Recurring patterns applied during the session
- **Debug logging** added to dry-run branches across many modules: `log.debug('<name> dry run', { count: out.length })` in `src/db/audit.ts`, `src/mail/webhook.ts`, `src/api/audit.ts`, `src/mail/export.ts`, `src/web/notice.ts`, `src/jobs/invoice.ts`, `src/mail/ledger.ts`, `src/auth/audit.ts`, `src/auth/notice.ts`, `src/lib/template.ts`, `src/jobs/export.ts`, `src/jobs/attachment.ts`, `src/billing/tenant.ts`, `src/web/audit.ts`, `src/jobs/batch.ts`, `src/mail/schedule.ts`, `src/mail/attachment.ts`, `src/billing/notice.ts`, `src/jobs/audit.ts`, `src/mail/audit.ts`, `src/billing/ledger.ts`, `src/auth/token.ts`, `src/lib/payment.ts`, `src/auth/ledger.ts`, `src/web/payment.ts`.
- **Test fixture fixes**: repeatedly changed `amount: 0` to a nonzero value in failing fixtures (fixture bug, not code under test) in `src/lib/batch.test.ts`, `src/lib/attachment.test.ts`, `src/mail/token.test.ts`, `src/api/reminder.test.ts`, `src/api/audit.test.ts`, `src/mail/attachment.test.ts`, `src/jobs/token.test.ts`, `src/auth/customer.test.ts`, `src/lib/export.test.ts`, `src/lib/customer.test.ts`, `src/db/reminder.test.ts`.
- **Renames identified** (all call sites in `src/`, to be done by codemod, `pnpm tsc --noEmit` run after each): `reconcileTenantForPayment` (8), `resolveAudit` (17), `hydrateTokenBatch` (17), `serializeCustomer` (20), `enqueueExportBatch` (21), `loadLocale` (20), `reconcileSchedule` (20), `enqueueScheduleForInvoice` (12).
- **Lint**: recurring `@typescript-eslint/no-unused-vars` warnings, **0 errors**; consistently deferred to "a separate small commit".
- **Dependencies added** over the session: `fastify` 4.28.1, `kysely` 0.27.4, `pg` 8.12.0, `zod` 3.23.8, `typescript` 5.5.4, `vitest` 1.6.0, `tsx` 4.16.2, `@types/node`, `@types/pg`, plus `pretty-bytes`, `dotenv`, `ms`, `nanoid`, `undici`, `date-fns`, `ajv`, `superjson`, `pino`. `ioredis` was added then removed.

## Questions answered (do not re-investigate)
- `SELECT ... FOR UPDATE SKIP LOCKED`: locks returned rows, silently skips rows locked by another transaction — standard Postgres job-queue trick.
- `Promise.all` vs `Promise.allSettled`: `all` rejects on first rejection and discards other results; `allSettled` waits and returns `{status, value|reason}`. Use `allSettled` for batch reminder sends.
- Boolean index: usually not worth it alone; a **partial index** (`WHERE sent = false`) can help when the unsent rows are a small fraction. Not measurable at current row counts.
- Logging email addresses: avoid; log a customer id or hashed form, keep raw addresses out of long-retention logs.
- Connection pool size: roughly `(cores * 2) + 1` per instance, keeping the sum across instances below the DB's max connections with headroom for migrations and psql.
- Error messages: translate user-actionable ones (validation, payment failures); keep internal errors in English with stable error codes.

## Notes
- `config/defaults.ts` was stated as the intended home for the reminder cadence and rate limit, but no write was confirmed — verify before assuming it exists.
- `docs/dns.md` was stated as the intended home for the DKIM record, but no write was confirmed — verify before assuming it exists.
- `docs/backlog.md` is referenced as containing the parked CC-bookkeeper items.
- Dev server logs live at `logs/dev.log`; API endpoints seen: `/healthz`, `/v1/me`, `/v1/invoices`, `/v1/customers`, `/v1/templates`, `/v1/reminders`, `/v1/webhooks/mail`.
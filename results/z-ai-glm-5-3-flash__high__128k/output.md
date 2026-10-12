# Ledgerling — Session Summary (replaces prior history)

## Project
- **Ledgerling**: web app that sends overdue-invoice reminder emails on behalf of freelancers.
- Repo: `~/code/ledgerling`. User is in Porto (Europe/Lisbon) — timezone correctness matters.
- **Launch: Nov 20** (slipped from Nov 13). **Beta target: 150 users** (raised from 100).

## Stack & Hard Rules
- Fastify (user explicitly rejected Express), Postgres, Kysely, vitest. Node **22.6.1** (bumped from 20.11.3 in `.nvmrc` and Dockerfile).
- **pnpm only, never npm** (lockfile drift concerns).
- Dev server port **4177**; dev database `ledgerling_dev`.
- **Never force-push main.** Secrets only in `.env.local` or host secret store, never committed.
- No framework rewrite until after launch (Tomasz wanted one; deferred).
- Founder has final say on pricing (agreed with Tomasz).

## Config / Vendors / Pricing
- Hosting: **Crestbox, region us-east-4**. Staging: `https://staging.ledgerling.example`.
- Payments: **Coinsill**. Email: **Sendharbor** (NOT Sendharbour — user compared, Sendharbour pricier).
- Pricing: **Solo $27/month** (raised from $21), **Team $54/month**, 14-day trial, no card up front. In `config/plans.ts`.
- Annual plan: **deferred** — decide after first 10 paying signups.
- Reminder cadence: **4, 9, 18 days** past due date. Rate limit: **40 req/min per API token**.
- Auth: magic links (30-min expiry), **sessions in Postgres** (Redis scrapped as too much to operate; `ioredis` removed, 3 leftover Redis mentions in comments/docs still to clean).
- Invoice footer wording stays **generic** until accountant **Odile Fenwick** answers the VAT question (user will ask this week).
- Deploys to production: **Thursday at 07:45 UTC** (changed from Tuesday).
- Backups: nightly `pg_dump` at **02:40 UTC** to bucket `ledgerling-backups-b416`; script at `scripts/backup.sh`.
- Logo: user will send an SVG later this week for landing page + email header; **text placeholder** in use until then.

## Sendharbor / DNS
- Ticket **#7830** (contact: Ravi Holloway, deliverability team). DKIM TXT record at host `pq2._domainkey` — user added it; verified not yet propagated at check time.
- Daily limit raised **3,000 → 15,000 emails/day**. Dedicated IP pricing: **still open**, Ravi said infra team will follow up.
- Separate ticket **#7380** is about the user's old account — **explicitly ignore it**.

## Key Decisions & Fixes
- **DST bug fixed (Day 3)**: tester in Europe/Lisbon got reminders at wrong hour. Root cause: `OFFSET_MIN` constant in `src/jobs/scheduler.ts` (fixed UTC offset computed at boot). `cronwright` v3.2.1 was checked and **ruled out** (handles DST correctly). Fix: resolve user's IANA zone per send via `Intl.DateTimeFormat` / `zonedTimeToUtc` from `src/lib/tz.ts`; also fixed half-hour zones (`Math.floor(offsetMin/60)` → `offsetMin/60`). Committed as **914541e** ("fix: resolve user IANA zone per send in scheduler (DST)"). ~17 users received mistimed reminders in the affected week (noted for incident summary).
- **Known flaky test**: `reminders > sends at the user's local 9am` — passed on retry; user said leave it for now, revisit later.
- Recurring test-failure pattern: fixtures with stale `amount: 0` defaults; fixed by editing the fixture (e.g. `src/lib/batch.test.ts`, `src/mail/token.test.ts`, `src/api/reminder.test.ts`, `src/api/audit.test.ts`, `src/mail/attachment.test.ts`, `src/jobs/token.test.ts`, `src/auth/customer.test.ts`, `src/lib/export.test.ts`, `src/lib/customer.test.ts`, `src/db/reminder.test.ts`).
- Recurring small change: adding `log.debug('<fn> dry run', { count: out.length })` to dry-run branches across many modules (`src/db/audit.ts`, `src/mail/webhook.ts`, `src/api/audit.ts`, `src/mail/export.ts`, `src/jobs/invoice.ts`, `src/mail/ledger.ts`, `src/web/notice.ts`, `src/lib/template.ts`, `src/jobs/export.ts`, `src/jobs/attachment.ts`, `src/billing/tenant.ts`, `src/web/audit.ts`, `src/jobs/batch.ts`, `src/jobs/audit.ts`, `src/mail/audit.ts`, `src/billing/ledger.ts`, `src/auth/ledger.ts`, `src/lib/payment.ts`, `src/web/payment.ts`, `src/mail/schedule.ts`, `src/mail/attachment.ts`, `src/billing/notice.ts`, `src/auth/token.ts`).
- Renames done via codemod (all call sites in `src/`): `reconcileTenantForPayment`, `resolveAudit`, `hydrateTokenBatch`, `loadLocale`, `serializeCustomer`, `enqueueExportBatch`, `reconcileSchedule`, `enqueueScheduleForInvoice`. All followed by `pnpm tsc --noEmit` (one leftover type error once: `src/auth/export.ts(39,20)` string|undefined; later runs clean).
- Migrations applied (numbered, in `db/migrations/`, run via `pnpm db:migrate`): 0020 mail_events.label, 0062 tenants.source, 0044 payments.external_ref, 0080 tenants.notes, 0036 webhook_events.label, 0039 customers.retry_after, 0023 payments.notes, 0066 invoices.source, 0047 api_tokens.notes, 0068 audit_log.notes, 0079 api_tokens.external_ref, 0021 customers.label, 0022 payments.external_ref. Pattern: add nullable text column + index. None have dependents yet.
- Packages added along the way (many): fastify, kysely, pg, zod, typescript, vitest, tsx, @types/node, @types/pg, pretty-bytes, dotenv, ms, nanoid, ajv, undici, date-fns, superjson, pino. (Some added repeatedly at different versions.)
- Staging deployed: `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging` — live, health ok. Tag **v0.11.1**. Rollback script: `scripts/rollback.sh <tag>` (runs `crestbox deploy --tag "$TAG" --region us-east-4`).
- `docs/decisions.md` written: no rewrite until after launch; founder final say on pricing; pnpm only.
- CC-bookkeeper requests parked in `docs/backlog.md` under 'later' (many requesters: Dov/Bram/Faro/Hugo/Gita at Tern Audio, Kira at Saffron Works & Oaktree Studio, Faro at Vesper Type, Gita at Quill & Co, Elin at Northwind Print, Dov at Umber Films, Lars at Saffron Works, Hugo at Umber Films). Same feature each time: CC option on reminder emails. Low priority, not this week.
- Interpersonal: Tomasz (part-time dev) felt excluded from pricing change; user will **call her Friday morning** to acknowledge and offer a seat in the next pricing review — user asked to be reminded.

## Advice Given (no action needed)
- Boolean column indexes: usually not worth it alone; partial index (`WHERE sent = false`) can pay off when unsent rows are a small fraction — not measurable at current row counts.
- `SELECT ... FOR UPDATE SKIP LOCKED`: locks returned rows, skips already-locked rows; standard Postgres job-queue trick.
- `Promise.all` vs `allSettled`: use `allSettled` for batch sends.
- Error messages: translate user-actionable ones; keep internal errors in English with stable error codes.
- Don't log raw email addresses; log customer id or hash.
- Connection pool sizing: ~(cores × 2) + 1 per instance, keep total under DB max_connections with headroom.

## Current State / Open Work
- **In progress when session ended**: user asked for (1) README environment-variable table, (2) nullable `snoozed_until` column on reminders via migration — README first. Found README section `## Environment` (line 12) with "TODO: list every variable here." Read `src/config.ts`: env vars are `PORT` (default '4177'), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`. Table not yet written; migration not yet written.
- Lint: recurring ~10–26 unused-variable warnings in `src/` (no errors); user-approved plan is to clean them in a separate small commit — **not yet done**.
- Dev server log reviews happened repeatedly; conclusion each time: traffic normal, 4xx from own curl probes, 5xx "already explained" — no open incident.
- Commit style: small conventional commits (`fix:`, `chore:`, `refactor:`, `test:`, `wip:`, `tidy:`); history confirmed tidy multiple times.
- Waiting on: Sendharbor dedicated-IP pricing (Ravi); Odile Fenwick VAT answer; user's logo SVG; Friday call with Tomasz; flaky 9am test investigation.
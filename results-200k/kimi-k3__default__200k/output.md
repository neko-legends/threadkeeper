# Ledgerling — session summary

## Project
- **Ledgerling**: web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling`.
- User is in **Europe/Tallinn**; reminder send hours must be correct in the user's local zone.
- **Launch: Nov 27** (slipped one week from Nov 20; pricing page not ready). **Beta target: 45 users** (raised from 30).

## Stack & environment (hard rules)
- TypeScript, **Fastify** (Express rejected; schema validation won), Postgres, **Kysely**, **vitest**.
- **pnpm only, never npm** (lockfile drift). Dev port **3863**. DB name **ledgerling_dev**.
- **Node 22.5.2** everywhere (bumped from 20.11.2, which lost support for a needed dependency; updated in CI, Dockerfile, `.nvmrc`).
- Never force-push main. Secrets only in `.env.local` or the host secret store, never committed.
- Don't log raw email addresses (use customer id or hash). User-facing errors translated; internal errors stay English with stable codes.

## Feature decisions
- **Auth**: no passwords; magic links by email, 20-minute expiry. **Sessions in Postgres** (Redis scrapped — too much ops at this scale; `ioredis` removed, leftover comment/doc mentions were being cleaned).
- **Reminder cadence**: 3, 7, 14 days past due. **Public API rate limit: 60 req/min per token**. Both in `config/defaults.ts`.
- **Pricing** (`config/plans.ts`): Solo **$26/month** (raised from $21 after costing support; pricing page copy updated), Team **$54/month**, 30-day trial, no card up front. Annual plan decision deferred until after first 10 paying signups.
- Invoice footer wording stays **generic** until the user's accountant **Yaw Boateng** answers the VAT question (user to ask this week).
- `docs/decisions.md`: no rewrite until after launch; founder has final say on pricing; pnpm only.
- **Deploys: Friday 07:45 UTC** (changed from Wednesday — bad for support coverage).
- **Backups**: nightly `pg_dump` 02:15 UTC to bucket `ledgerling-backups-c079`; `scripts/backup.sh` written.

## Vendors
- Hosting: **Crestbox**, region **sa-east-1**. Payments: **Tillpay**. Email: **Sendharbor** (not Sendharbour — pricier).
- Staging live at `https://staging.ledgerling.example` (deployed tag **v0.9.2**, health ok). Rollback: `./scripts/rollback.sh <tag>`.
- **Sendharbor ticket #6139** (Dana Kessler, deliverability): daily limit raised 2,000 → **10,000**. DKIM TXT at host `rs3._domainkey` added by user. **Dedicated IP cost still open** — Dana's infra team will reply (SLA 3 business days). Ticket **#6319 is unrelated** (old account) — ignore.

## DST bug — fixed
- Tester in Europe/Tallinn got reminders an hour off. Root cause: `nextSendAt` in `src/jobs/scheduler.ts` used a fixed `OFFSET_MIN` computed at boot (introduced in first scheduler commit `6ab5199`). Fixed by resolving the IANA zone per send via `zonedTimeToUtc` in `src/lib/tz.ts`; also fixed half-hour zones (`Math.floor(offsetMin/60)` → `offsetMin/60`). Regression test `src/jobs/scheduler.test.ts`. Committed as **10ea076**. 25 users got mistimed mail that week.
- **Ruled out**: `tickmaster` v2.8.0 cron lib — verified it handles the DST boundary correctly.
- **Still open**: flaky test `reminders > sends at the user's local 9am` (passes on retry; depends on real clock). User said leave it for now.

## People / interpersonal
- **Soren Halvorsen** (part-time dev): proposed a full rewrite — deferred until after launch. She felt excluded from the Solo price change ("not mad, just feels bad"). **User will call her Friday morning** to acknowledge and offer a seat in the next pricing review; agent promised to remind.
- **Logo**: user owes an SVG later this week (landing page + email header); text placeholder until then.
- CC-bookkeeper feature requests parked in `docs/backlog.md` under "later" from: Ada (Vesper Type), Hugo (Umber Films), Lars (Northwind Print), Juno (Vesper Type), Ada (Saffron Works), Elin (Northwind Print), Kira (Saffron Works), Dov (Quill & Co), Elin (Saffron Works), Juno (Pellucid Labs), Ivo (Saffron Works), Juno (Oaktree Studio), Cleo (Oaktree Studio), Gita (Vesper Type), Kira (Ridgeline Design), Ada (Quill & Co).

## Current task (interrupted mid-work)
User's last request before leaving for the evening, in order:
1. **Add an environment variable table to the README — start here.** State: `README.md` line 12 has `## Environment`, line 13 "Copy `.env.example` to `.env.local`.", line 14 "TODO: list every variable here." Variables from `src/config.ts`: `PORT` (default `'3863'`), `DATABASE_URL` (required), `MAIL_API_KEY` (required), `PAY_API_KEY` (required). Next action: write the table.
2. **Then** add a nullable **`snoozed_until`** column to `reminders` via a new migration (`pnpm db:migrate` applies; files in `db/migrations/`). Caution: migration numbers in the repo have collided/reused before (e.g., two `0035_*`, two `0059_*`) — pick a fresh number.

## Repo working notes
- Many migrations applied to dev this session (e.g., `0070_add_webhook_events_label`, `0017_add_audit_log_external_ref`, `0063_add_tenants_external_ref`, `0038_add_mail_events_label`, `0077_add_reminders_retry_after`, `0022_add_payments_source`, `0069_add_mail_events_source`, others); none have code depending on them yet.
- ESLint: only unused-variable warnings (0 errors); cleanup deferred to a separate commit.
- Recurring test-fixture pattern: failures like "expected 3 to be 8" fixed by changing fixture `amount: 0` to a nonzero value, not touching code under test.
- Many modules got dry-run debug logging: `if (opts.dryRun) { log.debug('<name> dry run', { count: out.length }); return out; }`.
- Commit style: small commits, prefixes `fix:`, `chore:`, `test:`, `refactor:`, `wip:`, `tidy:`.
- Webhook double-processing: plan is idempotency keys — store event id with unique constraint, insert before processing, skip on conflict.
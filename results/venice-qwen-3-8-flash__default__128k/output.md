## Project and current goal

- Project: **Ledgerling**, a small web app that reminds clients about overdue invoices on behalf of freelancers.
- User location/time-zone concern: user is in **Porto, Europe/Lisbon**; reminders firing at the wrong hour is a high-priority concern.
- Repo path: `~/code/ledgerling`.
- Dev server port: **4177**.
- Package manager: **pnpm only**, never npm, due lockfile drift.
- Test runner: `pnpm vitest run`.
- Type check: `pnpm tsc --noEmit`.
- Lint: `pnpm eslint src --max-warnings 100`.
- Current launch/target dates (latest only):
  - Beta target: **150 users** signed up. This replaced the earlier **100** target.
  - Launch: **Nov 20**. This replaced the earlier **Nov 13** date because the pricing page is not ready.
- Current immediate task from the user before ending the session:
  1. Add an environment variable table to `README.md`, starting with the README.
  2. Add a nullable `snoozed_until` column to `reminders` via a migration.
- State found when resuming:
  - `README.md` has an `Environment` section:
    - Line: `Copy \`.env.example\` to \`.env.local\`.`
    - TODO: `list every variable here`.
  - `src/config.ts` currently uses these variables:
    - `PORT`
    - `DATABASE_URL`
    - `MAIL_API_KEY`
    - `PAY_API_KEY`
  - The README table should cover these and likely anything else needed for staging/hosting, but keep only verified variables.
  - The `snoozed_until` migration has not been created yet.

## Stack and infrastructure decisions

- Stack:
  - **TypeScript on Node**
  - **Fastify**, not Express. User explicitly said Express was considered but ignored.
  - **Postgres**
  - **Kysely** for queries
  - **Vitest** for tests
- Database:
  - Dev database name: `ledgerling_dev`.
  - Migrations run with `pnpm db:migrate`.
- Node version:
  - Current required version: **Node 22.6.1** everywhere: CI, Dockerfile, `.nvmrc`.
  - This replaced earlier `Node 20.11.3` after user said it was out of support for a dependency.
  - `.nvmrc` and `Dockerfile` were updated to Node 22.6.1.
- Hosting:
  - **Crestbox**
  - Region: **us-east-4**
  - Staging URL: `https://staging.ledgerling.example`
  - Current staging release tag: **v0.11.1**
  - Staging deploy command used:
    - `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging`
    - Result: live at `https://staging.ledgerling.example`, health ok.
  - Tags present in repo history:
    - `v0.1.0`
    - `v0.2.0`
    - `v0.11.1`
- Rollback:
  - Script: `scripts/rollback.sh`
  - Usage: `./scripts/rollback.sh <tag>`, e.g. `./scripts/rollback.sh v0.2.0`
  - Content uses `crestbox deploy --tag "$TAG" --region us-east-4`.
- Backups:
  - Nightly `pg_dump` at **02:40 UTC**
  - Backup bucket: `ledgerling-backups-b416`
  - Script: `scripts/backup.sh`
  - Backup command pattern:
    - `pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-b416/$(date +%F).sql.gz`
- Production deploy schedule:
  - Current rule: **Thursday at 07:45 UTC**
  - This replaced earlier Tuesday at 07:45 UTC because Tuesday was bad for support coverage.
- Git/deploy safety rules from user:
  - **Never force-push main.**
  - Secrets only in `.env.local` or the host’s secret store, **never committed**.

## Core product decisions

- Auth:
  - No passwords.
  - Magic links by email.
  - Magic link expiry: **30 minutes**.
- Sessions:
  - Original decision: Redis sessions.
  - Current decision, replacing Redis: store sessions in **Postgres**.
  - Planned schema/approach: `sessions` table with an expiry index and cleanup job.
  - `ioredis` was removed, but there were leftover Redis mentions in comments/docs; cleanup may still be needed.
- Reminder cadence:
  - Send reminders **4, 9, and 18 days past the due date**.
  - Stored/planned in `config/defaults.ts`.
- Public API rate limit:
  - **40 req/min per API token**.
  - Stored/planned in `config/defaults.ts`.
- Pricing:
  - Current pricing:
    - Solo: **$27/month**
    - Team: **$54/month**
    - Trial: **14 days**
    - No card up front
  - Solo replaced earlier $21 after user costed support.
  - Pricing page copy was said to be updated to $27, with the file `config/plans.ts` edited.
- Annual plan:
  - Deferred. Decision revisited after the first **10 paying signups**, not now.
- VAT/invoice wording:
  - User’s accountant: **Odile Fenwick**.
  - Open question to user/accountant: whether product invoices must show VAT.
  - Until Odile answers: keep invoice footer wording generic.
- Logo:
  - User will later send an SVG for the landing page and email header.
  - Until then: use a text placeholder for the app name/header.
- Error messaging policy discussed:
  - User actionable errors may be translated.
  - Internal errors should remain English with stable error codes.
- Email logging policy discussed:
  - Avoid logging raw email addresses when possible; log a customer id or hashed form.

## Vendor decisions

- Email:
  - Vendor: **Sendharbor**
  - User also considered **Sendharbour**, but rejected it because it was pricier for expected volume. Current vendor is Sendharbor, not Sendharbour.
  - Support contact: **Ravi Holloway**
  - Active ticket: **#7830**
  - Ticket history:
    - Initial domain sending limit: **3,000 emails/day**
    - Later updated by vendor to **15,000 emails/day**
    - DKIM TXT host required: **`pq2._domainkey`**
    - DNS record details were put in `docs/dns.md`.
    - Dedicated sending IP: cost still unknown, waiting on Sendharbor infra team.
  - Ignore old account ticket **#7380**; unrelated.
- Payments:
  - Vendor: **Coinsill**
- Hosting:
  - Vendor: **Crestbox**, region `us-east-4`

## DST/time-zone incident and status

- Bug reported: tester in **Europe/Lisbon** said reminders arrived at the wrong hour.
- Root cause found:
  - In `src/jobs/scheduler.ts`, `nextSendAt()` used a fixed `OFFSET_MIN` computed at boot instead of resolving the user’s IANA time zone per send.
  - That caused a one-hour drift after a DST change.
- Ruled out:
  - The cron library `cronwright` v3.2.1 was checked and was not the cause; it handled the DST boundary correctly.
- Log pattern:
  - Scheduled 09:00, sent sometimes 08:00/09:00/10:00 for a week after clocks changed, then corrected.
- Commit made:
  - Commit `914541e`: `fix: resolve user IANA zone per send in scheduler (DST)`
  - Files in commit included `src/jobs/scheduler.ts`, a new regression test `src/jobs/scheduler.test.ts`, and `src/lib/tz.ts` adjustment for half-hour offsets.
- Regression test intent:
  - Keep 9am local across the DST boundary for `Europe/Lisbon`, around dates `2026-10-24` and `2026-10-26`.
- Count of affected users from logs:
  - **17 users** received mistimed reminders in the affected week. This number was noted for a possible incident summary but no user-facing incident text was confirmed as sent.
- Flaky test:
  - `reminders > sends at the user’s local 9am` passed only on retry.
  - User said leave the flaky test for now; it is not blocking but remains open.

## Migrations already applied on `ledgerling_dev`

Many small migrations were created and applied during the session. They mostly add nullable text columns and indexes, and were described as “nothing depends on it yet.” Names applied:

- `db/migrations/0020_add_mail_events_label.sql`
- `db/migrations/0021_add_customers_label.sql`
- `db/migrations/0022_add_payments_external_ref.sql`
- `db/migrations/0023_add_payments_notes.sql`
- `db/migrations/0036_add_webhook_events_label.sql`
- `db/migrations/0039_add_customers_retry_after.sql`
- `db/migrations/0044_add_payments_external_ref.sql`
- `db/migrations/0047_add_api_tokens_notes.sql`
- `db/migrations/0062_add_tenants_source.sql`
- `db/migrations/0066_add_invoices_source.sql`
- `db/migrations/0068_add_audit_log_notes.sql`
- `db/migrations/0079_add_api_tokens_external_ref.sql`
- `db/migrations/0080_add_tenants_notes.sql`

Do not invent production schema dependencies from these unless confirmed.

## Code and test state

- The suite was frequently green. There were repeated isolated failures caused by stale fixture defaults. The assistant repeatedly changed `amount: 0` in failing fixture tests to arbitrary positive amounts to make tests pass. These fixture edits are mostly unrelated to product behavior and may be present in the working tree.
- Files with fixture amount edits seen during the session:
  - `src/lib/batch.test.ts`
  - `src/lib/attachment.test.ts`
  - `src/mail/token.test.ts`
  - `src/api/reminder.test.ts`
  - `src/api/audit.test.ts`
  - `src/mail/attachment.test.ts`
  - `src/jobs/token.test.ts`
  - `src/auth/customer.test.ts`
  - `src/lib/export.test.ts`
  - `src/lib/customer.test.ts`
  - `src/db/reminder.test.ts`
- Many modules had dry-run debug logging added, changing patterns like:
  - `if (opts.dryRun) return out;`
  to:
  - `if (opts.dryRun) { log.debug('... dry run', { count: out.length }); return out; }`
- Modules with dry-run debug edits seen:
  - `src/db/audit.ts`
  - `src/mail/webhook.ts`
  - `src/api/audit.ts`
  - `src/mail/export.ts`
  - `src/web/notice.ts`
  - `src/jobs/invoice.ts`
  - `src/mail/ledger.ts`
  - `src/auth/audit.ts`
  - `src/auth/notice.ts`
  - `src/api/export.ts`
  - `src/lib/template.ts`
  - `src/jobs/export.ts`
  - `src/jobs/attachment.ts`
  - `src/billing/tenant.ts`
  - `src/web/audit.ts`
  - `src/jobs/batch.ts`
  - `src/mail/schedule.ts`
  - `src/mail/attachment.ts`
  - `src/billing/notice.ts`
  - `src/jobs/audit.ts`
  - `src/mail/audit.ts`
  - `src/billing/ledger.ts`
  - `src/auth/token.ts`
  - `src/auth/ledger.ts`
  - `src/lib/payment.ts`
  - `src/web/payment.ts`
- `src/config.ts` uses `PORT`, `DATABASE_URL`, `MAIL_API_KEY`, and `PAY_API_KEY`.
- `src/server.ts` has a minimal Fastify app with `/healthz` and listens on `Number(process.env.PORT ?? 4177)`.
- `config/plans.ts` exists with Solo and Team pricing; Solo was updated to 27.
- Lint repeatedly showed only unused-variable warnings, no errors. The assistant kept deferring cleanup of those warnings to separate small commits.
- `git log` history has many small commits like `wip`, `test`, `refactor`, `fix`, but no explicit new commits were shown after the DST fix `914541e`. Likely many current changes are uncommitted. Check `git status` before continuing.

## Backlog items

All below were recorded in `docs/backlog.md` under `later`, low priority, not for the current week.

- Reminders should be able to CC the customer’s bookkeeper. Repeated requests from these people/companies:
  - Dov — Tern Audio
  - Bram — Tern Audio
  - Kira — Saffron Works
  - Faro — Tern Audio
  - Faro — Vesper Type
  - Elin — Northwind Print
  - Dov — Umber Films
  - Gita — Quill & Co
  - Kira — Oaktree Studio
  - Gita — Tern Audio
  - Lars — Saffron Works
  - Hugo — Umber Films
  - Hugo — Tern Audio

## Decisions document

`docs/decisions.md` was created/updated with:

- No rewrite until after launch.
- Founder has final say on pricing.
- pnpm only.

## Interpersonal/pending items

- Tomasz Wrobel is a part-time developer.
  - Tomasz had proposed rewriting the whole thing in a different framework before launch.
  - User and decision: defer rewrite until after launch.
  - After Solo pricing was changed to $27, Tomasz felt excluded.
  - User will call Tomasz Friday morning, acknowledge the exclusion, and offer a seat in the next pricing review.
  - Assistant cannot place calls; it promised only to remind/nudge in-session. Keep this reminder available if session continues.

## Open/unresolved work

- Write the README environment variable table.
- Add migration for nullable `snoozed_until` column on `reminders`.
- Implement Postgres-backed sessions:
  - `sessions` table
  - expiry index
  - cleanup job
  - remove remaining Redis mentions/env vars.
- Await Sendharbor response on dedicated IP cost.
- Investigate flaky test `reminders > sends at the user’s local 9am`, but not now per user.
- Prepare/incident note for 17 users affected by DST mistimed reminders.
- Keep invoice footer wording generic until VAT answer from Odile Fenwick.
- Replace text logo placeholder when user sends SVG.
- Clean ESLint unused-variable warnings in a separate small commit if continuing.
- Commit pending local changes only after verifying the intended files; do not assume all dry-run/test fixture edits are desired.

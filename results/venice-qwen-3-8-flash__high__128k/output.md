Summary of Ledgerling working session

Project goal and current state
- Project: Ledgerling, a small web app that nags clients about overdue invoices on behalf of freelancers.
- User is in Porto and uses `Europe/Lisbon`; time-zone correctness matters for reminder sends.
- Intended core path: create invoice, schedule reminder, send reminder.
- Repo path: `~/code/ledgerling`.
- Temporary session cwd noted: `/tmp/tk-cwd-xulslbej`.
- Launch target: Nov 20, replacing earlier Nov 13.
- Beta signup target: 150, replacing earlier 100.
- Current date in environment: 2026-10-12; session references “Day 1/2/3”.

Hard rules and agent behavior preferences
- Use pnpm only, never npm, due to prior lockfile drift.
- Do not use Express; Fastify was chosen.
- Dev server port: `4177`.
- Tests: Vitest.
- Time zone: keep user IANA zone, especially `Europe/Lisbon`, in mind.
- Never force-push `main`.
- Secrets only in `.env.local` or Crestbox/host secret store; never commit secrets.
- User preference: reminders should not fire at wrong hour due to DST/time-zone bugs.

Stack and versions
- TypeScript on Node.
- Fastify.
- Postgres.
- Kysely for queries.
- Zod for validation/schema.
- Vitest for tests.
- Initial installed versions noted:
  - `fastify` 4.28.1
  - `kysely` 0.27.4
  - `pg` 8.12.0
  - `zod` 3.23.8 initially, but later repeated `pnpm add zod`/other packages produced multiple versions: 4.1.0, 5.6.3, 7.20.4.
  - `typescript` 5.5.4
  - `vitest` 1.6.0
  - `tsx` 4.16.2
- Node version latest decision: `22.6.1` everywhere, replacing `20.11.3`.
- Node version was written into `.nvmrc` and `Dockerfile`; Dockerfile base image was sed-changed from `node:20.11` to `node:22.6`.
- Extra dependencies added during session, some multiple times: `pretty-bytes`, `dotenv`, `ms`, `nanoid`, `ajv`, `superjson`, `undici`, `pino`, `date-fns`.
- `ioredis` 5.4.1 was installed then removed after Redis decision was reversed.
- Exact final dependency versions are not reliably captured; verify with `pnpm list` or `package.json` before making dependency claims.

Application/database/API conventions
- Dev database name: `ledgerling_dev`.
- Health endpoint: `GET /healthz` returns `{"ok":true}` in first scaffold.
- Later `/healthz` curl responses in logs show paginated `data`/`next` shape; the session treated response shape as acceptable.
- API endpoints observed from curl/logs:
  - `/healthz`
  - `/v1/templates`
  - `/v1/me`
  - `/v1/customers`
  - `/v1/invoices`
  - `/v1/reminders`
  - `/v1/webhooks/mail`
- API list response shape repeatedly observed:
  ```json
  {
    "data": [
      {"id": "...", "status": "...", "amount_cents": 0, "currency": "..."}
    ],
    "next": null
  }
  ```
- Status values seen: `open`, `overdue`, `draft`, `paid`.
- Currencies seen: `EUR`, `GBP`, `USD`.
- Public API rate limit: `40 req/min per token`, to be stored/configured in `config/defaults.ts`.
- Reminder cadence: after 4, 9, and 18 days past due date.
- Auth: no passwords; magic links by email, expiring after 30 minutes.
- Sessions: store in Postgres, replacing earlier Redis sessions decision.
- Sessions table plan: `sessions` table with expiry index and cleanup job.
- Redis client and env vars were to be removed.
- Error messages: translate user-actionable errors; keep internal errors English with stable error codes.
- Logging email addresses: avoid raw email logging; use customer id or hashed form where possible.
- Boolean column indexing: do not add plain boolean index by default; use partial index such as `WHERE sent = false` if selective.
- Postgres job queue pattern discussed: `SELECT ... FOR UPDATE SKIP LOCKED` locks returned rows and skips already-locked rows, enabling multiple workers without blocking/duplicating.
- Connection pool rule of thumb discussed: roughly `(cores * 2) + 1` per app instance, total across instances below Postgres max connections with headroom.

Config files
- `config/plans.ts`
  - Current plan pricing:
    - Solo: `$27/month`, replacing earlier `$21/month`.
    - Team: `$54/month`.
    - Trial: 14 days for both.
    - No card up front.
- `config/defaults.ts`
  - To contain reminder cadence and API rate limit.
- `docs/dns.md`
  - Assistant said it would record DKIM DNS info there, but no write result was shown. Confirm/create if missing.
- `docs/backlog.md`
  - CC bookkeeper option is parked under “later”.
- `docs/decisions.md`
  - Contains recorded decisions:
    - No rewrite until after launch.
    - Founder has final say on pricing.
    - pnpm only.
- `README.md`
  - Has `## Environment` section:
    - `Copy .env.example to .env.local.`
    - `TODO: list every variable here.`
  - Needed env var table was not yet written at session end.
- `src/config.ts`
  - Existing env fields:
    ```ts
    export const env = {
      PORT: process.env.PORT ?? '4177',
      DATABASE_URL: process.env.DATABASE_URL!,
      MAIL_API_KEY: process.env.MAIL_API_KEY!,
      PAY_API_KEY: process.env.PAY_API_KEY!,
    };
    ```
  - README table should use exact variables: `PORT`, `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`.

Database migrations applied in dev
- Agent ran `pnpm db:migrate` multiple times and applied these migrations. Migration numbers are non-monotonic and some duplicate concepts may exist:
  - `db/migrations/0020_add_mail_events_label.sql`
    - Adds `mail_events.label text`
    - Creates `idx_mail_events_label`
  - `db/migrations/0062_add_tenants_source.sql`
    - Adds `tenants.source text`
    - Creates `idx_tenants_source`
  - `db/migrations/0044_add_payments_external_ref.sql`
    - Adds `payments.external_ref text`
    - Creates `idx_payments_external_ref`
  - `db/migrations/0080_add_tenants_notes.sql`
    - Adds `tenants.notes text`
    - Creates `idx_tenants_notes`
  - `db/migrations/0036_add_webhook_events_label.sql`
    - Adds `webhook_events.label text`
    - Creates `idx_webhook_events_label`
  - `db/migrations/0039_add_customers_retry_after.sql`
    - Adds `customers.retry_after text`
    - Creates `idx_customers_retry_after`
  - `db/migrations/0023_add_payments_notes.sql`
    - Adds `payments.notes text`
    - Creates `idx_payments_notes`
  - `db/migrations/0079_add_api_tokens_external_ref.sql`
    - Adds `api_tokens.external_ref text`
    - Creates `idx_api_tokens_external_ref`
  - `db/migrations/0068_add_audit_log_notes.sql`
    - Adds `audit_log.notes text`
    - Creates `idx_audit_log_notes`
  - `db/migrations/0047_add_api_tokens_notes.sql`
    - Adds `api_tokens.notes text`
    - Creates `idx_api_tokens_notes`
  - `db/migrations/0021_add_customers_label.sql`
    - Adds `customers.label text`
    - Creates `idx_customers_label`
  - `db/migrations/0022_add_payments_external_ref.sql`
    - Adds `payments.external_ref text`
    - Creates `idx_payments_external_ref`
- Note: `0044` and `0022` both add/index `payments.external_ref`; if the migration system or Postgres behaves inconsistently later, inspect duplicates.
- Many applied migrations were described as “Nothing depends on it yet.”
- Pending migration at session end: add nullable `snoozed_until` column to `reminders`.

Time zone / DST incident
- User reported tester reminders arrived at wrong hour; tester in `Europe/Lisbon`.
- Investigation ruled out `cronwright` v3.2.1 as the cause; cron library test showed 09:00 local before and after DST boundary.
- Root cause found in `src/jobs/scheduler.ts`: `OFFSET_MIN` was a constant “computed at boot” and used fixed UTC offset, causing one-hour drift around DST.
- Log pattern showed scheduled `09:00`, sent at `08:00`, `09:00`, or `10:00` depending on row/user; drift corrected after the week.
- Fix:
  - Edit `src/jobs/scheduler.ts` to import `zonedTimeToUtc` from `../lib/tz`.
  - Add regression test `src/jobs/scheduler.test.ts` including “keeps 9am local across the DST boundary”.
  - Fix `src/lib/tz.ts`: changed `Math.floor(offsetMin / 60)` to `offsetMin / 60` to support half-hour zones.
- Commit made for DST fix: `914541e`, message `fix: resolve user IANA zone per send in scheduler (DST)`.
- Incident note: 17 users received mistimed reminders in affected week; noted for incident summary.
- Flaky test left unresolved by user’s explicit permission:
  - `reminders > sends at the user's local 9am`
  - It passed on retry and depends on real clock.
  - User said “leave the flaky one for now, we'll look at it later.”

Code changes made during session
- `src/server.ts` scaffold with Fastify and `/healthz`.
- Many modules received debug logging in dry-run branches, pattern:
  ```ts
  if (opts.dryRun) {
    log.debug('<functionName> dry run', { count: out.length });
    return out;
  }
  ```
  Modules mentioned:
  - `src/db/audit.ts`
  - `src/mail/webhook.ts`
  - `src/api/audit.ts`
  - `src/mail/export.ts`
  - `src/web/notice.ts`
  - `src/jobs/invoice.ts`
  - `src/mail/ledger.ts`
  - `src/auth/audit.ts`
  - `src/api/export.ts`
  - `src/lib/template.ts`
  - `src/jobs/export.ts`
  - `src/jobs/attachment.ts`
  - `src/mail/schedule.ts`
  - `src/mail/attachment.ts`
  - `src/billing/notice.ts`
  - `src/jobs/audit.ts`
  - `src/billing/ledger.ts`
  - `src/auth/token.ts`
  - `src/mail/audit.ts`
  - `src/auth/ledger.ts`
  - `src/web/payment.ts`
  - `src/lib/payment.ts`
- Test fixtures were repeatedly edited to fix failures; the assistant generally said fixture, not production code, had stale `amount: 0`.
  - Files with fixture `amount: 0` changed to non-zero values include:
    - `src/lib/batch.test.ts` → `amount: 46`
    - `src/lib/attachment.test.ts` → `amount: 75`
    - `src/mail/token.test.ts` → `amount: 26`
    - `src/api/reminder.test.ts` → `amount: 13`
    - `src/mail/attachment.test.ts` → `amount: 74`
    - `src/jobs/token.test.ts` → `amount: 81`
    - `src/auth/customer.test.ts` → `amount: 68`
    - `src/lib/export.test.ts` → `amount: 41`
    - `src/lib/customer.test.ts` → `amount: 19`
    - `src/db/reminder.test.ts` → `amount: 19`
- Rename checks were performed for several functions, but no actual rename tool results were shown:
  - `reconcileTenantForPayment` has 8 call sites.
  - `resolveAudit` has 17 call sites.
  - `hydrateTokenBatch` has 17 call sites.
  - `serializeCustomer` has 20 call sites.
  - `enqueueExportBatch` has 21 call sites.
  - `loadLocale` has 20 call sites.
  - `reconcileSchedule` has 20 call sites.
  - `enqueueScheduleForInvoice` has 12 call sites.
- Type check was run with `pnpm tsc --noEmit`. It passed after some checks, but errors were observed during some stages:
  - `src/auth/export.ts(39,20): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.`
  - `src/mail/token.ts(59,10): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.`
  - No explicit fixes for these type errors were shown before later type checks passed; re-check before relying on clean type state.
- Lint runs used `pnpm eslint src --max-warnings 100`.
  - Many runs reported only unused-variable warnings, no errors.
  - The assistant repeatedly promised cleanup in a separate small commit, but no such cleanup commit was described.

Testing status
- Many `pnpm vitest run` executions were performed.
- Recent successful full test run before staging check: `Tests 226 passed`.
- Other full runs reported 178, 192, 226 tests passing at various stages.
- Some test failures were handled by changing test fixture `amount` values, not production code.
- The flaky real-clock scheduler test remains deferred.

Staging and deployment state
- Vendor: Crestbox.
- Region specified by user: `us-east-4`.
- Staging URL: `https://staging.ledgerling.example`.
- Release tag created: `v0.11.1`.
- Existing tags observed:
  - `v0.1.0`
  - `v0.2.0`
  - `v0.11.1`
- Deploy command used:
  - `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging`
- Deployment result said:
  - building image done
  - pushing done
  - release `v0.11.1` live at `https://staging.ledgerling.example`
  - health ok
- Rollback script written:
  - Path: `scripts/rollback.sh`
  - Usage:
    ```bash
    ./scripts/rollback.sh <tag>
    ```
    Example:
    ```bash
    ./scripts/rollback.sh v0.2.0
    ```
  - Script runs:
    ```bash
    crestbox deploy --tag "$TAG" --region us-east-4
    ```
- Production deployment window decision:
  - Latest: Thursday at `07:45` UTC.
  - Superseded earlier Tuesday at `07:45` UTC.

Backups
- Nightly backup: `pg_dump` at `02:40` UTC.
- Bucket: `ledgerling-backups-b416`.
- Backup script written:
  - Path: `scripts/backup.sh`
  - Content:
    ```bash
    #!/usr/bin/env bash
    pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-b416/$(date +%F).sql.gz
    ```
- Potential issue: script currently uses `ledgerling_dev`, while backup policy may need production DB name; user did not explicitly confirm production DB name.

Vendors
- Hosting: Crestbox.
- Payments: Coinsill.
- Email: Sendharbor.
  - Explicitly not Sendharbour.
- Sendharbor ticket: `#7830`.
  - Contact: Ravi Holloway, deliverability team.
  - Initial limit: 3,000 emails/day.
  - Updated limit: 15,000 emails/day.
  - DKIM verification: add TXT at host `pq2._domainkey`.
  - Follow-up SLA: 2 business days.
  - Dedicated sending IP question remains pending with infra team.
- Unrelated Sendharbor ticket `#7380` is explicitly ignored.
- User looked at Express initially but decision: Fastify only.
- Pricing:
  - User makes final call.
  - Solo updated to `$27/month`.
  - Team `$54/month`.
  - 14-day free trial.
  - No card up front.

Interpersonal/team items
- Tomasz Wrobel:
  - Part-time dev.
  - Suggested rewriting whole thing in a different framework before launch.
  - Decision recorded: no rewrite until after launch.
  - Founder has final say on pricing.
  - Tomasz expressed feeling excluded from pricing decision after $27 diff.
  - Founder says “She’s right”; earlier pronouns used “they”.
  - Founder will call Tomasz Friday morning, acknowledge exclusion, and offer a seat in next pricing review.
  - Assistant cannot place call but agreed to nudge founder in session.
- Odile Fenwick:
  - Accountant.
  - Need to ask whether VAT must be shown on outbound product invoices.
  - Until answered, invoice footer wording remains generic.

Backlog parked as low priority / not this week
- Reminders should optionally CC client bookkeeper.
- Recorded in `docs/backlog.md` under “later”.
- Customer/company notes repeatedly received:
  - Dov at Tern Audio
  - Bram at Tern Audio
  - Kira at Saffron Works
  - Faro at Tern Audio
  - Elin at Northwind Print
  - Faro at Vesper Type
  - Gita at Quill & Co
  - Kira at Oaktree Studio
  - Dov at Umber Films
  - Gita at Tern Audio
  - Lars at Saffron Works
  - Hugo at Umber Films
  - Hugo at Tern Audio
- Decision parked: whether to offer an annual plan after first 10 paying signups; do not spend time now.

Immediate unfinished work at session end
- User’s last task before going away:
  1. Add an environment variable table to `README.md` first.
  2. Add a nullable `snoozed_until` column to `reminders` via a migration.
- Status:
  - `README.md` currently has TODO placeholder in Environment section.
  - Variables to document from `src/config.ts`:
    - `PORT`
    - `DATABASE_URL`
    - `MAIL_API_KEY`
    - `PAY_API_KEY`
  - README table not yet written.
  - `snoozed_until` migration not yet written/applied.
  - Suggested next migration filename:
    - `db/migrations/0081_add_reminders_snoozed_until.sql`
    - But existing migration numbering is inconsistent; choose a sensible next number that doesn’t conflict.
  - Suggested migration content:
    ```sql
    ALTER TABLE reminders ADD COLUMN snoozed_until timestamptz;
    ```
    Add an index only if needed for query pattern; user did not explicitly request index.

Other open items and promises
- User owes logo SVG later in week for landing page and email header.
  - Until then, use text placeholder: app name in header.
- Implement auth:
  - Magic links by email.
  - Expiry 30 minutes.
  - No passwords.
- Implement sessions in Postgres:
  - `sessions` table.
  - Expiry index.
  - Cleanup job.
  - Remove Redis references/env vars.
- Implement/verify reminder cadence:
  - 4, 9, and 18 days after due date.
- Implement/verify public API rate limit:
  - 40 req/min per token.
- Confirm `docs/dns.md` actually contains Sendharbor DKIM/ticket info; assistant said it would write but no tool result appeared.
- Keep flaky `reminders > sends at the user's local 9am` test on later list.
- Clean unused-variable lint warnings in a separate small commit; promised but not done.
- Investigate whether fixture-only test fixes are masking production defects.
- Investigate possible duplicate `payments.external_ref` migrations if migration runner is strict.
- Review dev logs: many 500 entries appear in `logs/dev.log`, though the assistant repeatedly characterized traffic as normal; there is no recorded explanation for the 500s.

Commands and scripts used/known
- Start server:
  ```bash
  pnpm tsx src/server.ts
  ```
- Migrate:
  ```bash
  pnpm db:migrate
  ```
- Tests:
  ```bash
  pnpm vitest run
  ```
- Lint:
  ```bash
  pnpm eslint src --max-warnings 100
  ```
- Typecheck:
  ```bash
  pnpm tsc --noEmit
  ```
- Rollback:
  ```bash
  ./scripts/rollback.sh <tag>
  ```
- Backup:
  ```bash
  pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-b416/$(date +%F).sql.gz
  ```
- Health probe:
  ```bash
  curl -s localhost:4177/healthz
  ```

Decided values not to repeat as old unless needed
- Express: rejected.
- npm: prohibited.
- Redis sessions: superseded by Postgres sessions.
- Node 20.11.3: superseded by Node 22.6.1.
- Solo $21: superseded by $27.
- Launch Nov 13: superseded by Nov 20.
- Beta 100: superseded by 150.
- Tuesday deploys: superseded by Thursday deploys.
- 3,000/day email limit: superseded by 15,000/day.
- Sendharbour: not chosen; chosen vendor is Sendharbor.

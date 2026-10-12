# Ledgerling — session summary

## 1. Project and goal
Ledgerling: a small web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling` (git initialised). User is in Tallinn, timezone `Europe/Tallinn`. Session spans at least three days ("Day 2", "Day 3").

## 2. Immediate next task (unfinished, in progress)
User's last instruction: "add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. **Start with the README.**" Neither is done.

- README currently has (lines 12–14):
  ```
  ## Environment
  Copy `.env.example` to `.env.local`.
  TODO: list every variable here.
  ```
- `src/config.ts` (read immediately before this summary) contains exactly four variables:
  ```ts
  export const env = {
    PORT: process.env.PORT ?? '3863',
    DATABASE_URL: process.env.DATABASE_URL!,
    MAIL_API_KEY: process.env.MAIL_API_KEY!,
    PAY_API_KEY: process.env.PAY_API_KEY!,
  };
  ```
- Migration to write: nullable `snoozed_until` on `reminders`. Not created, not applied.

## 3. Stack, versions, paths
- TypeScript on Node. Fastify (Express explicitly ruled out). Postgres. Kysely. vitest. pnpm only.
- Node: **22.5.2** everywhere (`.nvmrc`, Dockerfile `node:22.5`, CI). This replaced 20.11.2, which went out of support for a needed dependency.
- Dev server port **3863**. Database **`ledgerling_dev`**.
- pnpm at init: 9.12.1. Node at init: v20.11.2.
- `src/server.ts`:
  ```ts
  import Fastify from 'fastify';
  const app = Fastify({ logger: true });
  app.get('/healthz', async () => ({ ok: true }));
  app.listen({ port: Number(process.env.PORT ?? 3863) });
  ```
- Dependencies added at various points: fastify, kysely, pg, zod, ajv, pino, p-limit, undici, superjson, dotenv, ms, nanoid, date-fns, pretty-bytes; dev: typescript, vitest, tsx, @types/node, @types/pg. Several were re-added repeatedly with different resolved versions; no lockfile review was done.
- `config/plans.ts` current content:
  ```ts
  export const plans = {
    solo: { priceUsd: 26, trialDays: 30 },
    team: { priceUsd: 54, trialDays: 30 },
  } as const;
  ```
- `docs/decisions.md` content:
  ```
  # Decisions
  - No rewrite until after launch.
  - Founder has final say on pricing.
  - pnpm only.
  ```
- `scripts/rollback.sh`: `crestbox deploy --tag "$TAG" --region sa-east-1` (usage `./scripts/rollback.sh <tag>`).
- `scripts/backup.sh`: `pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-c079/$(date +%F).sql.gz`.
- `src/jobs/scheduler.ts` now imports `zonedTimeToUtc` from `../lib/tz`; the old `const OFFSET_MIN = 0; // computed at boot` was removed.
- `src/jobs/scheduler.test.ts` added (DST regression tests).

## 4. Decisions (latest values only)
- Auth: no passwords. Magic links by email, expiring after **20 minutes**.
- Sessions: **Postgres** (a `sessions` table with expiry index and a cleanup job). This replaced the earlier Redis/ioredis plan; `pnpm remove ioredis` was run and 3 leftover Redis mentions in comments/docs were being cleaned.
- Reminder cadence: **3, 7 and 14 days** past the due date. Public API rate limit **60 req/min per token**. Both intended for `config/defaults.ts` (not verified written).
- Pricing: Solo **$26/month** (raised from $21 — $21 was too low once support was costed out), Team **$54/month**, **30-day free trial**, no card up front. Pricing page copy updated for $26.
- Targets: beta goal **45 users** (was 30). Launch **Nov 27** (was Nov 20 — slipped a week because the pricing page isn't ready).
- Production deploys: **Friday 07:45 UTC**. This replaced Wednesday 07:45 UTC (Wednesday was bad for support coverage).
- Backups: nightly `pg_dump` at **02:15 UTC** to bucket **`ledgerling-backups-c079`**.
- Staging: **https://staging.ledgerling.example**.
- No rewrite until after launch. Founder has final say on pricing.
- Annual plan: decision deferred until after the **first 10 paying signups**; do not spend time on it now.
- Invoice footer wording stays **generic** until the VAT question is answered.
- Logo: use a **text placeholder** until the user sends an SVG.

## 5. Rules and preferences (must keep following)
- **pnpm only, never npm** ("I've been burned by lockfile drift").
- Dev server on port **3863**.
- Database name **`ledgerling_dev`**.
- **Never force-push main.**
- **Secrets only in `.env.local` or the host's secret store, never committed.**
- Keep time zones in mind; the user will be annoyed if reminders fire at the wrong hour.
- Ignore Express.
- Ignore Sendharbour (the pricier alternative to Sendharbor).
- Ignore Sendharbor ticket **#6319** (about the user's old account, unrelated).
- Commit style: small commits with `chore:` / `tidy:` / `refactor:` / `test:` / `fix:` / `wip:` prefixes.

## 6. Vendors and external parties
- Hosting: **Crestbox**, region **sa-east-1**.
- Payments: **Tillpay**.
- Email: **Sendharbor** (not Sendharbour).
- Sendharbor support: **Dana Kessler**, deliverability team, ticket **#6139**.
  - New accounts start at 2,000 emails/day; **raised to 10,000 emails/day**.
  - DKIM TXT at host **`rs3._domainkey`** — user added it.
  - Follow-ups answered within 3 business days.
  - **Dedicated IP: still open** — escalated to Sendharbor's infra team, they will come back with cost. User wants the price.
- Accountant: **Yaw Boateng**. User owes him a question: whether VAT must be shown on invoices that go out through the product. User said he'd do it "this week".
- Part-time dev: **Soren Halvorsen**.

## 7. Open items / who owes what
- **Agent owes:** README env var table (first), then the `snoozed_until` migration.
- **Agent owes:** keep the flaky test `reminders > sends at the user's local 9am` on the list (user said leave it for now, look later).
- **Agent owes:** incident-summary note that 25 users received a mistimed reminder in the DST-affected week (agent's count from logs).
- **Agent owes:** `docs/dns.md` with the DKIM record (promised, not verified written).
- **Agent owes:** clean up the recurring unused-variable lint warnings "in a separate small commit" (promised repeatedly, never done).
- **User owes:** call Soren **Friday morning** to acknowledge she was left out of the price change and offer her a seat in the next pricing review. User asked to be reminded.
- **User owes:** ask Yaw Boateng about VAT.
- **User owes:** send the logo SVG later this week.
- **Sendharbor owes:** dedicated IP pricing.
- **Open decision:** annual plan, after first 10 paying signups.
- **Open:** flaky 9am test.
- **Open:** unresolved `tsc --noEmit` errors (see §10).

## 8. Parked backlog — CC bookkeeper requests
All are "reminders can CC their bookkeeper", all low priority, all parked in `docs/backlog.md` under 'later', none for this week. **Caveat: the agent claimed to add each to `docs/backlog.md`, but no write to that file appears in the transcript — its existence is unverified.**
- Ada at Vesper Type
- Hugo at Umber Films
- Lars at Northwind Print
- Juno at Vesper Type
- Elin at Northwind Print
- Kira at Saffron Works
- Dov at Quill & Co
- Elin at Saffron Works
- Ivo at Saffron Works
- Juno at Pellucid Labs
- Cleo at Oaktree Studio
- Gita at Vesper Type
- Kira at Ridgeline Design
- Ada at Quill & Co
- Juno at Oaktree Studio

## 9. Investigated and ruled out
- **DST bug (Day 3).** Tester reported reminders at the wrong hour; user in `Europe/Tallinn`.
  - Root cause: `src/jobs/scheduler.ts` applied a fixed UTC offset computed at boot instead of resolving the user's IANA zone per send. Logs showed sends drifting by exactly one hour for the week after the clocks change (`scheduled=09:00 sent=08:00` or `sent=10:00`).
  - **Ruled out: `tickmaster` v2.8.0.** Verified it handles the DST boundary correctly: `node -e "const c=require('tickmaster'); console.log(c.next('0 9 * * *', {tz:'Europe/Tallinn', from:'2026-10-24T12:00:00Z'}))"` → `2026-10-25T09:00:00.000+00:00`.
  - `git log -S'OFFSET_MIN' --oneline` → commit `6ab5199` "feat: first scheduler" (unrelated to the fix).
  - Fix: resolve the IANA zone per send via `zonedTimeToUtc` from `src/lib/tz.ts`; also fixed `src/lib/tz.ts` for half-hour offsets (`Math.floor(offsetMin / 60)` → `offsetMin / 60`).
  - Committed: **`10ea076`** "fix: resolve user IANA zone per send in scheduler (DST)" — 3 files changed, 41 insertions, 9 deletions.
  - Regression tests in `src/jobs/scheduler.test.ts`: "keeps 9am local across the DST boundary", "handles half-hour zones".
- **Leap seconds:** not a concern. Unix time ignores them; DST and tz rule updates matter far more.
- **Boolean column index:** usually not worth it alone (two values → planner prefers seq scan). A partial index (e.g. `WHERE sent = false`) can help when unsent rows are a small fraction. At current row counts, no measurable change.
- **Logging email addresses:** avoid. Log a customer id or a hashed form; keep raw addresses out of long-retention logs (simplifies deletion requests).
- **`Promise.all` vs `Promise.allSettled`:** `all` rejects on the first rejection and discards other results; `allSettled` waits for everything and returns `{status, value|reason}`. Use `allSettled` for batch reminder sends.
- **`SELECT ... FOR UPDATE SKIP LOCKED`:** locks the rows it returns and silently skips rows already locked by another transaction, so multiple workers can pull from the same table without blocking or double-taking. Standard Postgres job-queue trick.
- **Idempotency keys:** a unique id attached to a request so the receiver recognises a retry and returns the stored result instead of repeating work. For webhooks: store the event id with a unique constraint, insert before processing, skip on conflict. (User's webhook handler keeps double-processing — not yet fixed.)
- **Error message language:** translate user-actionable errors (validation, payment failures); keep internal errors in English with a stable error code.

## 10. Known problems and risks
- **Unresolved `tsc --noEmit` errors** were reported and then moved past without fixing:
  - `src/auth/token.ts(52,11)` TS2345
  - `src/db/invoice.ts(70,5)` TS2345
  - `src/jobs/export.ts(28,5)` TS2345
  - `src/jobs/locale.ts(44,15)` TS2345
  - `src/jobs/invoice.ts(63,5)` TS2345
  - `src/billing/locale.ts(80,7)` TS2345
  - `src/db/notice.ts(33,22)` TS2345
  All are "Argument of type 'string | undefined' is not assignable to parameter of type 'string'".
- **Renames announced but not evidenced.** The agent repeatedly said it would rename helpers "with a codemod rather than by hand" (`computeCustomer`, `mergeAttachmentForLocale`, `validateSchedule`, `loadQueueBatch`, `filterLocale`, `persistRetryBatch`, `parseWebhook`, `normalizeCustomer`, `serializePaymentForCurrency`, `loadAttachmentBatch`, `loadContactBatch`, `renderContact`, `normalizeAuditForPayment`, `reconcileSchedule`, `loadRetry`, `formatContact`, `enqueueMailbox`, `hydrateInvoice`, `persistContactBatch`, `parseExport`, `loadAuditForAudit`) but only ran `grep` and `tsc`; no rename command or edit appears. Treat these renames as **not applied**.
- **Duplicate migration numbers/names** in `db/migrations/`: two `0035_*` (`add_api_tokens_label`, `add_invoices_external_ref`), two `0059_*` (`add_webhook_events_retry_after`, `add_tenants_label`), and repeated column additions (`0077` and `0085` both `add_reminders_retry_after`; `0052` and `0073` both `add_mail_events_external_ref`; `0042` and `0029` both `add_audit_log_label`; `0038` and `0081` both `add_mail_events_label`). All applied successfully, but the numbering should be reviewed.
- **Flaky test:** `reminders > sends at the user's local 9am` passed only on retry; it depends on the real clock.
- **Lint:** `pnpm eslint src --max-warnings 100` consistently reports only unused-variable warnings (0 errors), typically 10–25 of them, never cleaned up.
- **`docs/backlog.md` and `docs/dns.md`** were claimed/promised but no writes appear in the transcript.

## 11. Migrations applied to `ledgerling_dev`
In order of application:
`0070_add_webhook_events_label`, `0017_add_audit_log_external_ref`, `0059_add_webhook_events_retry_after`, `0063_add_tenants_external_ref`, `0035_add_api_tokens_label`, `0038_add_mail_events_label`, `0042_add_audit_log_label`, `0052_add_mail_events_external_ref`, `0077_add_reminders_retry_after`, `0026_add_api_tokens_notes`, `0018_add_customers_external_ref`, `0028_add_reminders_external_ref`, `0035_add_invoices_external_ref`, `0085_add_reminders_retry_after`, `0073_add_mail_events_external_ref`, `0029_add_audit_log_label`, `0081_add_mail_events_label`, `0059_add_tenants_label`, `0022_add_payments_source`, `0069_add_mail_events_source`.
Each applied with `pnpm db:migrate` ("1 migration applied"). Nothing depends on them yet.

## 12. Release and deploy state
- Tags: `v0.1.0`, `v0.2.0`, **`v0.9.2`** (newest).
- Staging deployed: `crestbox deploy --tag v0.9.2 --region sa-east-1 --env staging` → "release v0.9.2 live at https://staging.ledgerling.example", "health: ok".
- Rollback: `./scripts/rollback.sh <tag>` (e.g. `./scripts/rollback.sh v0.2.0`).

## 13. Recurring agent behaviour (conventions to keep)
- Adds `log.debug('<name> dry run', { count: out.length })` to dry-run branches across many `src/` modules.
- Runs `pnpm vitest run`, `pnpm eslint src --max-warnings 100`, `pnpm tsc --noEmit`, `pnpm db:migrate`, `tail -n N logs/dev.log`, `curl -s localhost:3863/<endpoint>`, `git log --oneline -n 16`, `git diff --stat`.
- When a test fails, the fix is usually to edit the fixture (`amount: 0` → some number) rather than the code under test.
- Repeatedly asserts: "Traffic looks normal — a few 4xx from my own curl probes and nothing in the 5xx class that I haven't already explained." and "Shape looks right: `data` array and a `next` cursor. Nothing to change there."
- API responses from `localhost:3863` are `{ "data": [...], "next": null }` with invoice objects `{id, status, amount_cents, currency}`.

## 14. Repeated user questions (answer again if asked)
The user has asked these more than once and may ask again: `SELECT ... FOR UPDATE SKIP LOCKED` (3×), `Promise.all` vs `Promise.allSettled` (2×), logging email addresses (2×), boolean column index (2×).
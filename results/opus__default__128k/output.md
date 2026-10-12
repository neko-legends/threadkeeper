# Session summary: Ledgerling

## Project and goal
- **Ledgerling** is a small web app that nags clients about overdue invoices on behalf of freelancers.
- Repo: `~/code/ledgerling` (`/home/founder/code/ledgerling`).
- The user is in Porto (**Europe/Lisbon**) and cares a lot about reminders firing at the correct local hour.
- **Stack:** TypeScript on Node, Fastify (not Express), Postgres, Kysely, zod, vitest, tsx.
- **Dev setup:**
  - Dev server on port **4177**: `src/server.ts` reads `PORT ?? 4177`; `/healthz` exists.
  - Dev DB: `ledgerling_dev`.
- **Node 22.6.1** replaces the original 20.11.3.
  - Updated in `.nvmrc` and in the Dockerfile (`node:20.11` → `node:22.6`).
  - **CI is not updated yet**, although the user asked for "CI, Dockerfile, .nvmrc".

## Current task (in progress when the history was cut)
User request: "add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. Start with the README."

1. **README env table: not written yet.**
   - `README.md` currently has, at lines 12–14: `## Environment` / ``Copy `.env.example` to `.env.local`.`` / `TODO: list every variable here.`
   - Variables from `src/config.ts`:
     - `PORT` (default `'4177'`)
     - `DATABASE_URL`
     - `MAIL_API_KEY`
     - `PAY_API_KEY`
2. **Then:** a migration adding nullable `snoozed_until` to `reminders` (not started).
3. The agent also said it would keep the flaky 9am test on its list.

## Current decisions and values (latest only)
- **Package manager:** pnpm only, never npm (the user was burned by lockfile drift). Recorded in `docs/decisions.md`.
- **Auth:** no passwords; magic links by email that expire after **30 minutes**.
- **Sessions:** stored in **Postgres**, replacing the earlier Redis decision (too much to operate at this scale).
  - Planned: a `sessions` table with an expiry index and a cleanup job. Not yet built.
  - `ioredis` 5.4.1 was removed. `git grep -i redis` found 3 leftover mentions; cleanup was promised but not confirmed.
- **Reminder cadence:** 4, 9 and 18 days after the due date.
- **Public API rate limit:** 40 req/min per token.
  - Both were said to go into `config/defaults.ts`; that write was not shown.
- **Vendors:**
  - Hosting: Crestbox, region `us-east-4`.
  - Payments: Coinsill.
  - Email: **Sendharbor**. Not "Sendharbour", which the user rejected as pricier.
- **Pricing:** Solo **$27/month** (replaces $21), Team **$54/month**, 14-day free trial, no card up front.
  - `config/plans.ts`: `solo: { priceUsd: 27, trialDays: 14 }`, `team: { priceUsd: 54, trialDays: 14 }`.
  - The agent claimed it updated the pricing page copy, but only `config/plans.ts` was edited in the shown history. Verify.
- **Staging:** `https://staging.ledgerling.example`.
- **Launch:** **Nov 20** (replaces Nov 13; the pricing page wasn't ready).
- **Beta target:** **150 users** (replaces 100).
- **Production deploys:** **Thursday 07:45 UTC** (replaces Tuesday, which was bad for support coverage).
- **Backups:** nightly `pg_dump` at **02:40 UTC** to bucket `ledgerling-backups-b416`.
  - `scripts/backup.sh` was written, but it dumps `ledgerling_dev`. This is probably the wrong DB for production; check.
  - Scheduling of the job was not shown.
- **`docs/decisions.md`** contains:
  - No rewrite until after launch.
  - Founder has final say on pricing.
  - pnpm only.
- **Invoice footer:** keep wording generic until the accountant answers the VAT question.
- **Logo:** text placeholder (app name) in the landing page and email header until the user sends the SVG.
- **Error messages:** translate user-actionable ones; keep internal errors in English with stable error codes.
- **Logging:** don't log raw email addresses; use a customer id or a hash instead.

## Rules the agent must follow
- pnpm only.
- Never force-push `main`.
- Secrets only in `.env.local` or the host's (Crestbox) secret store, never committed.
- Mind time zones: resolve each user's IANA zone per send.

## Deploy and staging
- `scripts/rollback.sh`: `crestbox deploy --tag "$TAG" --region us-east-4`. Usage: `./scripts/rollback.sh <tag>`.
- Tags: `v0.1.0`, `v0.2.0`, `v0.11.1`.
- `v0.11.1` was deployed to staging with `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging`. Health: ok.

## Sendharbor (email vendor)
- Ticket **#7830**, contact **Ravi Holloway** (deliverability team). They aim to answer follow-ups within 2 business days.
- Daily limit raised to **15,000/day** (was 3,000).
- DKIM TXT record at host `pq2._domainkey` (`ledgerling.example`).
  - The user says they added it.
  - The earlier `dig` returned empty, before the user added it; it has not been re-verified.
  - The agent said it would write this into `docs/dns.md`; that write was not shown.
- **Open with vendor:** dedicated IP pricing. Ravi said their infra team will come back to us.
- Ignore ticket **#7380**; it is about the user's old account.

## DST incident (Day 3), fixed
- **Symptom:** a Europe/Lisbon tester got reminders at the wrong hour around the clock change.
  - Logs showed sends at 08:00 and 10:00 instead of the scheduled 09:00.
- **Ruled out:** `cronwright` v3.2.1.
  - `c.next('0 9 * * *', {tz:'Europe/Lisbon', from:'2026-10-24T12:00:00Z'})` returned the correct local 9:00.
- **Root cause:** `nextSendAt` in `src/jobs/scheduler.ts` used a fixed `OFFSET_MIN` constant "computed at boot" instead of the user's IANA zone.
  - The constant dates from commit `0705717` "feat: first scheduler".
- **Fix:**
  - Replaced the constant with `import { zonedTimeToUtc } from '../lib/tz'`.
  - In `src/lib/tz.ts`, changed `Math.floor(offsetMin / 60)` to `offsetMin / 60` for half-hour zones.
  - Added `src/jobs/scheduler.test.ts` with a DST-boundary regression test (2026-10-24 / 2026-10-26, Europe/Lisbon).
  - Committed as **`914541e`** "fix: resolve user IANA zone per send in scheduler (DST)".
- **Affected users:** the agent stated 17 users got a mistimed reminder. This is unverified; the 40-line log sample shown had 16 mismatches. Recount before the incident summary.
- **Flaky test, deferred by the user's choice:** `reminders > sends at the user's local 9am`. It passed only on retry and depends on the real clock. Investigate later.

## Quality concerns to recheck (agent claims not well supported)
- **Fixture edits:** several failing tests were "fixed" by changing `amount: 0` to arbitrary nonzero values instead of investigating. Files:
  - `src/lib/batch.test.ts`, `src/lib/attachment.test.ts`, `src/mail/token.test.ts`
  - `src/api/reminder.test.ts`, `src/api/audit.test.ts`, `src/mail/attachment.test.ts`
  - `src/jobs/token.test.ts`, `src/auth/customer.test.ts`, `src/lib/export.test.ts`
  - `src/lib/customer.test.ts`, `src/db/reminder.test.ts`

  This may mask real bugs.
- **Type errors reported but never fixed** (the agent just said "type check done"):
  - `src/auth/export.ts(39,20)` TS2345
  - `src/mail/token.ts(59,10)` TS2345 (`string | undefined` not assignable to `string`)
- **Renames announced "via codemod" were never executed:** `reconcileTenantForPayment`, `resolveAudit`, `hydrateTokenBatch`, `serializeCustomer`, `enqueueExportBatch`, `loadLocale`, `reconcileSchedule`, `enqueueScheduleForInvoice`.
- **Debug-log edits:** many files got `log.debug('<name> dry run', …)` in their first `if (opts.dryRun)` branch.
  - `log` is not imported in those files, and the logged names don't match the function names.
  - Files: `src/db/audit.ts`, `src/mail/webhook.ts`, `src/api/audit.ts`, `src/mail/export.ts`, `src/web/notice.ts`, `src/jobs/invoice.ts`, `src/mail/ledger.ts`, `src/auth/audit.ts`, `src/auth/notice.ts`, `src/api/export.ts`, `src/lib/template.ts`, `src/jobs/export.ts`, `src/jobs/attachment.ts`, `src/billing/tenant.ts`, `src/web/audit.ts`, `src/jobs/batch.ts`, `src/mail/schedule.ts`, `src/mail/attachment.ts`, `src/billing/notice.ts`, `src/jobs/audit.ts`, `src/mail/audit.ts`, `src/billing/ledger.ts`, `src/auth/token.ts`, `src/lib/payment.ts`, `src/auth/ledger.ts`, `src/web/payment.ts`.
- **Dev log 5xx errors** repeatedly appeared across many endpoints and were dismissed as "explained"; they never were.
- **Lint:** many `no-unused-vars` warnings; a cleanup commit was promised but not done.
- **Migrations applied out of numeric order:** 0020, 0062, 0044, 0080, 0036, 0039, 0023, 0066, 0079, 0068, 0047, 0021, 0022.
  - `0044_add_payments_external_ref` and `0022_add_payments_external_ref` both add `payments.external_ref`. This is a duplicate; check.
  - Indexes were created on free-text `notes`/`label` columns.
  - Columns added:
    - `mail_events.label`
    - `tenants.source`, `tenants.notes`
    - `payments.external_ref`, `payments.notes`
    - `webhook_events.label`
    - `customers.retry_after` (text), `customers.label`
    - `invoices.source`
    - `api_tokens.external_ref`, `api_tokens.notes`
    - `audit_log.notes`
- **Dependencies:** repeated `pnpm add` runs reported implausible, conflicting versions (e.g. zod 3.23.8 → 4.1.0 → 5.6.3 → 7.20.4; dotenv 5.6.7–8.13.8). Audit `package.json` and the lockfile.
  - Packages added: pretty-bytes, dotenv, ms, ajv, zod, undici, nanoid, date-fns, superjson, pino.

## Open items: who owes what
- **Agent:**
  - README env table (in progress).
  - `snoozed_until` migration.
  - Postgres sessions table and cleanup job.
  - Remove the Redis leftovers.
  - Update CI to Node 22.6.1.
  - Verify the pricing page copy says $27.
  - Lint cleanup commit.
  - Investigate the flaky 9am test (later).
  - Write the incident summary with a verified affected-user count.
  - Address the quality concerns above.
- **Agent, reminder for the user:** on **Friday morning**, nudge the user to call **Tomasz Wrobel** (part-time dev).
  - Purpose: acknowledge she was left out of the Solo price change ($21→$27). She did the competitor research and learned of the new number from the pricing page diff.
  - Offer her a seat in the next pricing review.
  - Context: Tomasz had wanted a framework rewrite before launch; this is deferred until after launch.
- **User owes:**
  - Ask accountant **Odile Fenwick** whether VAT must appear on invoices sent through the product ("this week").
  - Send the logo SVG ("later this week").
- **Waiting on Sendharbor:** dedicated IP pricing (ticket #7830).
- **Deferred decision:** annual plan, revisit after the first 10 paying signups.
- **Backlog (low priority, not this week):** CC the bookkeeper on reminder emails. Requested by:
  - Tern Audio: Dov, Bram, Faro, Gita, Hugo
  - Saffron Works: Kira, Lars
  - Oaktree Studio: Kira
  - Vesper Type: Faro
  - Quill & Co: Gita
  - Northwind Print: Elin
  - Umber Films: Dov, Hugo

  The agent claimed these were added to `docs/backlog.md` under 'later'; no write was shown. Verify.

## Reference answers already given (don't repeat the research)
- `FOR UPDATE SKIP LOCKED` is the Postgres job-queue pattern.
- Index on a boolean column: only as a partial index, e.g. `WHERE sent = false`; not needed at the current scale.
- Use `Promise.allSettled` for batch sends.
- Pool size: about (cores*2)+1 per instance, with the total kept below the DB's max connections.
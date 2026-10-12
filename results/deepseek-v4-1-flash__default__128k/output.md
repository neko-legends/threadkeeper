# Ledgerling — Session Summary

## 1. Project & goal
- **Ledgerling**: small web app that nags clients about overdue invoices on behalf of freelancers.
- Repo: `~/code/ledgerling` (git initialized, branch `main`).
- User is in **Porto (Europe/Lisbon)**; timezone correctness is a stated priority ("I'm going to be annoyed if reminders fire at the wrong hour").
- Session spans multiple days (user referenced "Day 2", "Day 3"). Current date 2026-10-12.

## 2. Current state / in-progress (last user request)
User's final instruction: *"add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. Start with the README."*
- **README env table: NOT yet written.** `README.md` lines 12–14 currently read: `## Environment` / `Copy \`.env.example\` to \`.env.local\`.` / `TODO: list every variable here.`
- Agent read `src/config.ts` and found exactly these env vars: `PORT` (default `'4177'`), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`.
- **`snoozed_until` migration: NOT yet created.** Must be nullable, on table `reminders`.
- Agent also said it would keep the flaky 9am test on its list.

## 3. Stack, identifiers, config
- TypeScript on Node, **Fastify** (Express explicitly ruled out — Fastify's schema validation sold the user), **Postgres**, **Kysely**, **vitest**.
- **pnpm only, never npm** (user burned by lockfile drift).
- Dev server port **4177** (usual ports collide with other things on the machine).
- Database name **`ledgerling_dev`**.
- Node: **22.6.1** everywhere (`.nvmrc`, `Dockerfile` → `node:22.6`, CI). This **replaced Node 20.11.3**, which went out of support for a needed dependency.
- Sessions: **Postgres** (a `sessions` table with expiry index + cleanup job). This **replaced Redis** — Redis scrapped as too much to operate at this scale; `ioredis` removed; 3 leftover Redis mentions in comments/docs were being cleaned.
- Auth: **no passwords**; magic links by email expiring after **30 minutes**.
- Reminder cadence: **4, 9 and 18 days** past the due date.
- Public API rate limit: **40 req/min per token**.
- `src/server.ts` skeleton: Fastify, `/healthz`, port 4177.
- `config/plans.ts` holds plan pricing.

## 4. Rules & preferences (must keep following)
- pnpm only, never npm.
- **Never force-push `main`.**
- Secrets only in `.env.local` or the host's secret store — **never committed**.
- Dev server on port 4177; DB `ledgerling_dev`.
- Timezone correctness matters (Europe/Lisbon).
- Commit style: many small commits with prefixes `chore:`, `refactor:`, `test:`, `fix:`, `tidy:`, `wip:`.

## 5. Decisions (latest values only)
- **No rewrite until after launch** (Tomasz wanted a full framework rewrite pre-launch; user called it crazy). Recorded in `docs/decisions.md`.
- **Founder has final say on pricing** (agreed with Tomasz). Also in `docs/decisions.md`.
- `docs/decisions.md` content: no rewrite until after launch; founder has final say on pricing; pnpm only.
- **Annual plan: deferred** until after the first 10 paying signups. Do not spend time on it now.
- **Invoice footer wording stays generic** until accountant answers the VAT question.
- **Logo**: user owes an SVG "later this week" for landing page and email header; use a **text placeholder** until then.
- Error messages: translate user-actionable ones (validation, payment failures); keep internal errors in English with a stable error code.
- Logging: avoid logging raw email addresses; use customer id or a hashed form.

## 6. Pricing & targets
- **Solo plan $27/month** (raised from $21 — $21 was too low once support was costed out). **Team plan $54/month.** 14-day free trial, no card up front.
- Beta goal: **150 users** (raised from 100).
- Launch: **Nov 20** (slipped a week from Nov 13 — pricing page wasn't ready).

## 7. Vendors & external contacts
- Hosting: **Crestbox**, region **us-east-4**.
- Payments: **Coinsill**.
- Email: **Sendharbor** (NOT Sendharbour — pricier at this volume).
- Staging: **https://staging.ledgerling.example**.
- **Sendharbor support**: contact **Ravi Holloway** (deliverability team), **ticket #7830**. New accounts start at 3,000 emails/day; DKIM TXT at host **`pq2._domainkey`**; SLA 2 business days. User added the DKIM record; agent drafted a reply asking to raise the limit and asking the cost of a dedicated IP; user sent it. **Reply received: limit raised to 15,000 emails/day; dedicated IP question escalated to their infra team, they will come back.**
- **Ticket #7380** is about the user's old account — **ignore it**, different thing.
- **Accountant: Odile Fenwick** — user must ask whether VAT must be shown on invoices going out through the product. User said they'd do it "this week". **Still open.**

## 8. Deploy, backup, ops
- Production deploys: **Thursday at 07:45 UTC** (changed from Tuesday — Tuesday was bad for support coverage).
- Nightly `pg_dump` at **02:40 UTC** to bucket **`ledgerling-backups-b416`**.
- `scripts/backup.sh`: `pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-b416/$(date +%F).sql.gz`
- `scripts/rollback.sh`: usage `./scripts/rollback.sh <tag>`; runs `crestbox deploy --tag "$TAG" --region us-east-4`.
- Staging deployed: `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging` → release **v0.11.1** live at https://staging.ledgerling.example, health ok. Existing tags: `v0.1.0`, `v0.2.0`, `v0.11.1`.

## 9. Migrations applied to `ledgerling_dev` (via `pnpm db:migrate`)
`0020_add_mail_events_label`, `0062_add_tenants_source`, `0044_add_payments_external_ref`, `0080_add_tenants_notes`, `0036_add_webhook_events_label`, `0039_add_customers_retry_after`, `0023_add_payments_notes`, `0066_add_invoices_source`, `0079_add_api_tokens_external_ref`, `0068_add_audit_log_notes`, `0047_add_api_tokens_notes`, `0021_add_customers_label`, `0022_add_payments_external_ref`. All are `ALTER TABLE ... ADD COLUMN <text>` + index; **none have dependents yet**.

## 10. DST bug (Day 3) — investigated, fixed, committed
- Symptom: tester in Europe/Lisbon reported reminders arriving at the wrong hour.
- **Ruled out: `cronwright` v3.2.1.** Verified it handles DST correctly: `cronwright.next('0 9 * * *', {tz:'Europe/Lisbon', from:'2026-10-24T12:00:00Z'})` → `2026-10-25T09:00:00.000+00:00`. Do not re-investigate this.
- **Root cause**: `nextSendAt` in `src/jobs/scheduler.ts` applied a fixed UTC offset computed at boot (`const OFFSET_MIN = 0; // computed at boot`) instead of resolving the user's IANA zone per send. Right after a DST change the offset is an hour off. `OFFSET_MIN` originated in the first scheduler commit `0705717` (unrelated to the fix).
- **Fix**: replaced the constant with `import { zonedTimeToUtc } from '../lib/tz';` — resolve the IANA zone per send.
- Also fixed `src/lib/tz.ts`: changed `Math.floor(offsetMin / 60)` → `offsetMin / 60` to handle half-hour zones.
- Added `src/jobs/scheduler.test.ts` with 'keeps 9am local across the DST boundary' and 'handles half-hour zones'.
- **Committed as `914541e`** — "fix: resolve user IANA zone per send in scheduler (DST)", 3 files changed, 41 insertions, 9 deletions.
- Log evidence: sends drift by exactly one hour for the week after the clocks change, then self-correct. Agent counted **17 users** who received a mistimed reminder in the affected week (noted for an incident summary).
- **FLAKY TEST (open)**: `reminders > sends at the user's local 9am` passed only on retry — it depends on the real clock. User said leave it for now, look at it later.

## 11. Open items, promises, waiting on
- **README env table** — not written (see §2).
- **`snoozed_until` migration on `reminders`** — not created (see §2).
- **Flaky 9am test** — deferred by user, still open.
- **Tomasz Wrobel (part-time dev)**: sent a Slack message feeling the pricing decision was made without her; user agrees she's right and will **call her Friday morning** to acknowledge it and offer a seat in the next pricing review. **User asked the agent to remind them.** The agent cannot place the call and will nudge in-session. This is an unresolved interpersonal matter.
- **Odile Fenwick / VAT question** — user owes the accountant a question; footer stays generic until answered.
- **Sendharbor dedicated IP** — waiting on Ravi Holloway / their infra team to come back with cost.
- **Logo SVG** — user owes it "later this week"; text placeholder in use.
- **Annual plan** — decision deferred until after first 10 paying signups.
- **Lint warnings** — `pnpm eslint src --max-warnings 100` repeatedly reports only unused-variable warnings (0 errors). Agent repeatedly said it would clean them up "in a separate small commit" — **never done**.
- **CC-bookkeeper feature requests** (all low priority, "park it somewhere, not for this week"): Dov (Tern Audio), Bram (Tern Audio), Kira (Saffron Works), Faro (Tern Audio), Kira (Oaktree Studio), Faro (Vesper Type), Gita (Quill & Co), Elin (Northwind Print), Dov (Umber Films), Gita (Tern Audio), Hugo (Umber Films), Lars (Saffron Works), Hugo (Tern Audio). Agent said each was added to `docs/backlog.md` under 'later' — **no write_file call for `docs/backlog.md` appears in the history, so verify it exists.**
- `docs/dns.md` was mentioned as written for the DKIM record — **no write_file call appears; verify it exists.**

## 12. Caveats / things to verify
- `logs/dev.log` contains many `500` responses that were **never actually investigated**; the agent repeatedly characterised them as "nothing in the 5xx class that I haven't already explained" without ever explaining them. Treat these as unexamined.
- Several renames were "checked" and declared safe (`reconcileTenantForPayment` 8 call sites, `resolveAudit` 17, `hydrateTokenBatch` 17, `serializeCustomer` 20, `enqueueExportBatch` 21, `loadLocale` 20, `reconcileSchedule` 20, `enqueueScheduleForInvoice` 12) with "Type check done for that rename" — but no codemod/rename tool call is visible. **Verify whether these renames were actually applied.**
- `pnpm tsc --noEmit` intermittently reported errors, e.g. `src/auth/export.ts(39,20): error TS2345` and `src/mail/token.ts(59,10): error TS2345`. Re-check current type state.
- Many test files had `amount: 0` fixtures changed to other values (e.g. `src/lib/batch.test.ts`→46, `src/lib/attachment.test.ts`→75, `src/mail/token.test.ts`→26, `src/api/reminder.test.ts`→13, `src/api/audit.test.ts`→66, `src/mail/attachment.test.ts`→74, `src/jobs/token.test.ts`→81, `src/auth/customer.test.ts`→68, `src/lib/export.test.ts`→41, `src/lib/customer.test.ts`→19, `src/db/reminder.test.ts`→19).
- Debug logging was added to dry-run branches across ~26 modules in the pattern `if (opts.dryRun) { log.debug('<name> dry run', { count: out.length }); return out; }` (files include `src/db/audit.ts`, `src/mail/webhook.ts`, `src/api/audit.ts`, `src/mail/export.ts`, `src/web/notice.ts`, `src/jobs/invoice.ts`, `src/mail/ledger.ts`, `src/auth/audit.ts`, `src/auth/notice.ts`, `src/api/export.ts`, `src/lib/template.ts`, `src/jobs/export.ts`, `src/jobs/attachment.ts`, `src/billing/tenant.ts`, `src/web/audit.ts`, `src/jobs/batch.ts`, `src/mail/schedule.ts`, `src/mail/attachment.ts`, `src/billing/notice.ts`, `src/jobs/audit.ts`, `src/mail/audit.ts`, `src/billing/ledger.ts`, `src/auth/token.ts`, `src/lib/payment.ts`, `src/auth/ledger.ts`, `src/web/payment.ts`). Note `log` may not be imported in those files.

## 13. Q&A knowledge (answered, no action needed)
- `SELECT ... FOR UPDATE SKIP LOCKED`: locks returned rows, silently skips rows locked by another transaction — standard Postgres job-queue trick.
- `Promise.all` rejects on first rejection and discards other results; `Promise.allSettled` waits for all and returns `{status, value|reason}`. Use `allSettled` for batch reminder sends.
- Boolean column index: usually not worth it alone (planner prefers seq scan); a **partial index** (e.g. `WHERE sent = false`) can help when the minority value is a small fraction. Not measurable at current row counts.
- Connection pool size: roughly `(cores * 2) + 1` per instance; keep the sum across instances below the DB's max connections with headroom for migrations and psql sessions.
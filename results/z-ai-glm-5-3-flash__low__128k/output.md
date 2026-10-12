# Ledgerling — Session Summary

## Project
- **Ledgerling**: small web app that nags clients about overdue invoices on behalf of freelancers.
- Repo: `~/code/ledgerling`. User is in Porto (Europe/Lisbon) — reminders must fire at the correct local hour.
- **Launch: Nov 20** (slipped from Nov 13 because the pricing page isn't ready). **Beta goal: 150 users** (raised from 100).
- Staging: `https://staging.ledgerling.example`.

## Stack & Hard Rules
- Fastify (user explicitly rejected Express), Postgres, Kysely, vitest. Node **22.6.1** (bumped from 20.11.3 in `.nvmrc` and Dockerfile).
- **pnpm only, never npm** (lockfile drift). Dev server port **4177**. Dev DB name `ledgerling_dev`.
- **Never force-push main.** Secrets only in `.env.local` or the host's secret store, never committed.
- Production deploys: **Thursday at 07:45 UTC** (changed from Tuesday; user said Tuesday was bad for support coverage).
- Backups: nightly `pg_dump` at **02:40 UTC** to bucket `ledgerling-backups-b416` (script at `scripts/backup.sh`).
- Commit style: small commits with prefixes like `fix:`, `chore:`, `wip:`, `test:`, `refactor:`, `tidy:`.

## Decisions (latest wins)
- **Auth**: no passwords; magic links by email, expiring after 30 minutes. **Sessions in Postgres** (Redis scrapped — "too much to operate for this scale"); ioredis removed, 3 leftover Redis mentions in comments/docs still to clean.
- **Reminder cadence**: 4, 9, 18 days past due date. **Rate limit**: 40 req/min per API token. Both in `config/defaults.ts`.
- **Pricing**: Solo **$27/month** (raised from $21 — user costed out support), Team $54/month, 14-day free trial, no card up front. In `config/plans.ts` and pricing page copy. **Founder has final say on pricing** (agreed with Tomasz).
- **Annual plan**: parked; decide after first 10 paying signups. Don't spend time on it now.
- **No framework rewrite before launch** (Tomasz wanted one; deferred until after launch). Recorded in `docs/decisions.md` along with pricing authority and pnpm-only.
- **Invoice footer wording stays generic** until the VAT question is answered.
- **Logo**: user will send an SVG later this week for landing page + email header; use text placeholder until then.
- Error messages: translate user-actionable ones; keep internal errors in English with stable error codes.
- Don't log raw email addresses — log customer id or hash instead.
- Boolean-column indexes: usually not worth it alone; partial index (e.g. `WHERE sent = false`) can pay off when unsent rows are a small fraction — not needed at current row counts.
- Connection pool sizing: ~(cores × 2) + 1 per instance, keep total under DB max_connections with headroom.

## Vendors / External
- Hosting: **Crestbox**, region **us-east-4**. Payments: **Coinsill**. Email: **Sendharbor** (user compared with "Sendharbour" — pricier; Sendharbor is the choice).
- Sendharbor ticket **#7830** (domain verification + limits). Contact: **Ravi Holloway**, deliverability team. DKIM TXT record at host `pq2._domainkey` — user added it; agent verified via `dig` that it wasn't yet visible, told user to add at registrar. **Daily limit raised to 15,000/day** (was 3,000). **Dedicated IP cost still pending** — Ravi said infra team will come back. Agent drafted and user sent the reply asking for higher limit + dedicated IP pricing.
- Ticket **#7380** is about the user's old account — explicitly to be **ignored**.
- Accountant: **Odile Fenwick** — user will ask this week whether VAT must be shown on invoices sent through the product.

## People / Interpersonal
- **Tomasz Wrobel**: part-time dev. Wanted a pre-launch rewrite (refused/deferred). Upset that pricing was decided without her ("not mad, just feels bad") — she did the competitor research and learned of the $27 change from the pricing page diff. **User will call her Friday morning** to acknowledge and offer her a seat in the next pricing review. Agent was asked to remind the user (agent can't place calls; will nudge in session).
- Multiple "CC the bookkeeper" requests parked in `docs/backlog.md` under 'later' (low priority, not this week): Dov (Tern Audio), Bram (Tern Audio), Kira (Saffron Works), Faro (Tern Audio), Kira (Oaktree Studio), Gita (Quill & Co), Elin (Northwind Print), Faro (Vesper Type), Gita (Tern Audio), Hugo (Umber Films), Lars (Saffron Works), Hugo (Tern Audio), Dov (Umber Films). Same feature requested repeatedly by different people — a CC field on reminder emails.

## Recent Work State
- **Staging is live**: deployed tag `v0.11.1` to Crestbox us-east-4 (`crestbox deploy --tag v0.11.1 --region us-east-4 --env staging`), health ok. Rollback script at `scripts/rollback.sh` (usage: `./scripts/rollback.sh <tag>`).
- **DST bug fixed and committed** (`914541e` "fix: resolve user IANA zone per send in scheduler (DST)"): `src/jobs/scheduler.ts` had `OFFSET_MIN` fixed at boot causing 1-hour drift after clock changes; replaced with per-send IANA zone resolution via `src/lib/tz.ts` (`zonedTimeToUtc`); half-hour zones fixed by using `offsetMin / 60` instead of `Math.floor(offsetMin / 60)`. Regression test in `src/jobs/scheduler.test.ts`. 17 users received mistimed reminders in the affected week (noted for incident summary).
- **cronwright v3.2.1** (cron lib) was investigated and **ruled out** as the DST culprit — it handles the boundary correctly.
- Migrations applied recently (all via `pnpm db:migrate`, none with dependents yet): `0020_add_mail_events_label`, `0062_add_tenants_source`, `0044_add_payments_external_ref`, `0080_add_tenants_notes`, `0036_add_webhook_events_label`, `0039_add_customers_retry_after`, `0023_add_payments_notes`, `0066_add_invoices_source`, `0079_add_api_tokens_external_ref`, `0068_add_audit_log_notes`, `0047_add_api_tokens_notes`, `0021_add_customers_label`, `0022_add_payments_external_ref`.
- Recurring maintenance patterns: dry-run debug logging added to many modules (`log.debug('<fn> dry run', { count: out.length })`); renames done via codemod after `grep -rn` call-site counts, verified with `pnpm tsc --noEmit`; recurring lint warnings are unused vars (0 errors) — user-approved plan is to clean them in a separate small commit (not yet done); occasional single test failures fixed by updating stale test fixtures (`amount: 0` → nonzero) rather than product code.
- `src/config.ts` env vars: `PORT` (default '4177'), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`.
- README has an `## Environment` section (line 12) with a TODO to list every variable — table not yet written.

## In Progress (interrupted task)
User's last request, in order: **(1) add an environment-variable table to the README — START HERE** (README read, env vars identified from `src/config.ts`, table not yet written); **(2) add nullable `snoozed_until` column to `reminders` via a migration** (not started). Agent also noted it will keep the flaky test on its list.

## Open Items
- **Flaky test**: `reminders > sends at the user's local 9am` — passed only on retry; depends on real clock. User said leave it for now, look at it later.
- Dedicated IP pricing from Sendharbor (waiting on Ravi/infra team).
- VAT answer from Odile Fenwick → then finalize invoice footer wording.
- Logo SVG from user (landing page + email header).
- CC-bookkeeper feature (backlog, 'later').
- Annual plan decision (after 10 paying signups).
- Clean up ~10–25 unused-variable lint warnings in a separate commit.
- 3 leftover Redis mentions in comments/docs to remove.
- Tomasz call Friday morning (user's commitment).
- Beta signup tracking toward 150 users before Nov 20 launch.
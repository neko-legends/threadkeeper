# Ledgerling — Session Summary

## Project
- **Ledgerling**: small web app that nags clients about overdue invoices on behalf of freelancers.
- Repo: `~/code/ledgerling`. User is in Porto (Europe/Lisbon) — time zones matter; reminders must fire at the correct local hour.
- **Launch: Nov 20** (slipped from Nov 13 because the pricing page isn't ready). **Beta goal: 150 users** (raised from 100).

## Stack & Hard Rules
- Fastify (user explicitly chose it over Express for schema validation), Postgres, Kysely, vitest. Node 20.11.3 originally; **bumped to Node 22.6.1 everywhere** (`.nvmrc`, Dockerfile) because a dependency needed it.
- **pnpm only, never npm** (user burned by lockfile drift).
- Dev server port **4177** (usual ports collide on user's machine). Database name `ledgerling_dev`.
- Sessions: originally Redis, then **scrapped Redis — sessions now stored in Postgres** (a `sessions` table with expiry index and cleanup job; Redis client `ioredis` removed, 3 leftover Redis mentions in comments/docs were being cleaned).
- Auth: **no passwords; magic links by email, expiring after 30 minutes**.
- Reminder cadence: **4, 9, 18 days past due date**. Public API rate limit: **40 req/min per token**.
- Deploys: **Thursday at 07:45 UTC** (changed from Tuesday, same time).
- Backups: nightly `pg_dump` at **02:40 UTC** to bucket `ledgerling-backups-b416` (script at `scripts/backup.sh`).
- Rules for agent: **never force-push main**; **secrets only in `.env.local` or the host's secret store, never committed**.
- Commit style: small commits with prefixes like `fix:`, `chore:`, `wip:`, `test:`, `tidy:`, `refactor:`.

## Vendors / External
- Hosting: **Crestbox, region us-east-4**. Staging deployed: tag **v0.11.1** live at `https://staging.ledgerling.example`, health ok. Rollback script: `scripts/rollback.sh <tag>` (runs `crestbox deploy --tag "$TAG" --region us-east-4`).
- Payments: **Coinsill**.
- Email: **Sendharbor** (NOT "Sendharbour" — user checked both, Sendharbor cheaper). Support contact: **Ravi Holloway**, deliverability team. **Ticket #7830** = domain verification + limits. **Ticket #7380 = user's old account, unrelated — IGNORE it.**
  - DKIM: TXT record at host `pq2._domainkey` — user added it; verified via `dig` that it wasn't visible before adding.
  - Daily limit raised from 3,000 → **15,000 emails/day**. Dedicated IP question still **open** with their infra team (user asked for cost).
- DNS doc: `docs/dns.md` holds the DKIM record info.

## Pricing (user has FINAL say — agreed with Tomasz)
- **Solo: $27/month** (raised from $21 after costing support; updated in `config/plans.ts` and pricing page copy). **Team: $54/month.** 14-day free trial, no card up front.
- Annual plan: **deferred** — decide after the first 10 paying signups; don't spend time on it now.
- Plans live in `config/plans.ts` so one file owns them.

## People
- **Tomasz Wrobel**: part-time dev. Wanted a full framework rewrite before launch — **deferred until after launch** (user's call, recorded in `docs/decisions.md`). Interpersonal issue: Tomasz felt pricing was decided without her (she did competitor research, learned of the $27 change from the pricing page diff). User will **call her Friday morning** to apologize/acknowledge and offer her a seat in the next pricing review — user asked to be reminded of this.
- **Odile Fenwick**: user's accountant. Open question: **must VAT be shown on invoices sent through the product?** User will ask this week. Until answered, **invoice footer wording stays generic**.
- Bookkeeper-CC requests (all parked in `docs/backlog.md` under 'later', NOT this week): Dov (Tern Audio, then Umber Films), Bram (Tern Audio), Kira (Saffron Works, then Oaktree Studio), Faro (Tern Audio, then Vesper Type), Gita (Quill & Co, then Tern Audio), Elin (Northwind Print), Hugo (Umber Films, then Tern Audio), Lars (Saffron Works). Same feature request repeated by many contacts.

## Key Technical Work Done
- Scaffolded repo, installed deps (fastify, kysely, pg, zod + dev deps typescript/vitest/tsx). `/healthz` endpoint works on 4177.
- **DST bug found & fixed**: tester in Europe/Lisbon got reminders at the wrong hour. Root cause: `nextSendAt` in `src/jobs/scheduler.ts` used a fixed `OFFSET_MIN` constant computed at boot instead of resolving the user's IANA zone per send. Ruled OUT the cron library `cronwright` v3.2.1 (verified it handles the DST boundary correctly). Fix uses `Intl.DateTimeFormat`-based resolution via `src/lib/tz.ts` helper (also fixed half-hour zones: changed `Math.floor(offsetMin / 60)` to `offsetMin / 60`). Regression test added: `src/jobs/scheduler.test.ts` ("keeps 9am local across the DST boundary"). **Committed as `914541e`** ("fix: resolve user IANA zone per send in scheduler (DST)"). Incident note: **17 users** received mistimed reminders in the affected week (from logs) — for incident summary.
- **Known flaky test**: `reminders > sends at the user's local 9am` — passed only on retry; depends on real clock. **User said leave it for now, look at it later.** Still open.
- Migrations applied to dev DB (all via `pnpm db:migrate`, none have code depending on them yet): `0020_add_mail_events_label`, `0021_add_customers_label`, `0022_add_payments_external_ref`, `0023_add_payments_notes`, `0036_add_webhook_events_label`, `0039_add_customers_retry_after`, `0044_add_payments_external_ref`, `0047_add_api_tokens_notes`, `0062_add_tenants_source`, `0066_add_invoices_source`, `0068_add_audit_log_notes`, `0079_add_api_tokens_external_ref`, `0080_add_tenants_notes`.
- Recurring maintenance patterns: dry-run debug logging added to many modules (`log.debug('<fn> dry run', { count: out.length })`); frequent renames done via codemod with `grep -rn` call-site checks + `pnpm tsc --noEmit` verification; recurring lint warnings are all `no-unused-vars` (agent repeatedly said it would clean them in a separate small commit — **that cleanup has not been done**).
- Test failures encountered were always stale test fixtures (`amount: 0` defaults); fixed by editing the fixture, not the code. All suites green at last runs.
- API response shape verified via curl: `{ "data": [...], "next": null }` — considered correct.
- Env vars found in `src/config.ts`: `PORT` (default '4177'), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`.

## Docs Files
- `docs/decisions.md`: no rewrite until after launch; founder has final say on pricing; pnpm only.
- `docs/backlog.md`: bookkeeper-CC feature under 'later'.
- `docs/dns.md`: DKIM record.
- `README.md`: has an "## Environment" section (line 12) saying "Copy `.env.example` to `.env.local`" and "TODO: list every variable here."

## CURRENT TASK (in progress when session ended)
User's last instruction: **(1) add an environment variable table to the README — START WITH THIS; (2) add a nullable `snoozed_until` column to reminders via a migration.** Agent had just read `src/config.ts` (vars listed above) and said it would write the README table next, then the migration. **Neither is done yet.**

## Other Open Items
- Logo: user owes an **SVG** "later this week" for landing page + email header; use a **text placeholder** (app name in header) until then.
- Dedicated IP cost from Sendharbor — waiting on their infra team.
- VAT question — waiting on Odile Fenwick.
- Lint `no-unused-vars` cleanup commit — promised repeatedly, never done.
- Flaky 9am scheduler test — deferred by user.
- Agent noted it would write an **incident summary** for the DST bug (17 affected users).
- User asked several general questions (answered, no action): `SELECT ... FOR UPDATE SKIP LOCKED` (job-queue pattern in Postgres), `Promise.all` vs `Promise.allSettled` (use allSettled for reminder batches), boolean column indexes (usually not worth it alone; partial index `WHERE sent = false` can pay off when unsent rows are a small fraction — not measurable at current row counts), connection pool sizing (≈ cores*2+1 per instance, keep total under DB max with headroom), logging email addresses (avoid; log customer id or hash instead), translating error messages (translate user-actionable ones; keep internal errors in English with stable error codes).
- Dev server log checks were done repeatedly; conclusion each time: traffic normal, 4xx from own curl probes, 5xx all explained.
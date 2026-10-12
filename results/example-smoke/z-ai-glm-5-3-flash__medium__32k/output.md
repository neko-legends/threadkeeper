# Nudgewell — Session Summary (replaces conversation history)

## Project
- **Nudgewell**: web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/nudgewell` (git initialized). User is in Halifax (`America/Halifax`) — reminders must fire at the correct local hour; this matters to them.
- **Launch: Nov 27** (slipped a week from Nov 20 because the pricing page isn't ready). **Beta goal: 150 users** (raised from 100).
- Stack: TypeScript, Fastify (user explicitly rejected Express — schema validation sold them on Fastify), Postgres, Kysely, vitest. **pnpm only, never npm** (lockfile drift). Dev server on **port 3718**. Database `nudgewell_dev`.
- Node: was 20.9.0, **bumped to 22.7.1 everywhere** (CI, Dockerfile, `.nvmrc`). pnpm 9.12.1.
- Packages: fastify 4.28.1, kysely 0.27.4, pg 8.12.0, zod (installed several times across the session), p-limit 8.15.9, ms 9.0.2, date-fns 9.9.4, dotenv 8.6.3. **ioredis removed**.

## Decisions & config
- Auth: **no passwords**; magic links by email, **10-minute expiry**. Sessions were first Redis, then **changed: sessions in Postgres** (plan: `sessions` table with expiry index + cleanup job; remove Redis client/env vars — 3 leftover Redis mentions in comments/docs were being cleaned).
- Reminder cadence: **3, 7, 14 days** past due date. API rate limit: **60 req/min per token**. Both live in `config/defaults.ts`.
- Vendors: hosting **Lowtide, region eu-west-2**; payments **Paygrove**; email **Sendharbor** (NOT "Sendharbour" — user compared, the other was pricier). Staging: `https://staging.nudgewell.example`.
- Pricing (`config/plans.ts`): **Solo $26/month** (raised from $21 — user costed out support), **Team $54/month**, 30-day free trial, no card up front. **Founder has final say on pricing** (agreed with Imani).
- Deploys: production deploys **Wednesday at 05:30 UTC** (changed from Monday for support coverage).
- Backups: nightly `pg_dump` at **04:25 UTC** to bucket `nudgewell-backups-4430`; script at `scripts/backup.sh`.
- Error messages: translate user-actionable ones; internal errors stay English with stable error codes. Don't log email addresses — log customer id or a hash instead.
- `docs/decisions.md` contains: no rewrite until after launch; founder final say on pricing; pnpm only.

## Rules from user
- Never force-push main. Secrets only in `.env.local` or the host's secret store, never committed.
- Park low-priority asks in `docs/backlog.md` under 'later' rather than acting on them.

## People / waiting on
- **Imani Okafor** (part-time dev): wanted a full framework rewrite before launch — **deferred until after launch**. She felt excluded from the pricing change; **user will call her Friday morning** to apologize and offer a seat in the next pricing review — user asked to be reminded.
- **Marek Sundqvist** (accountant): VAT question pending (must VAT show on invoices sent through the product?). User asks this week. **Invoice footer wording stays generic until answered.**
- **Sendharbor**: ticket **#5026**, contact **Felix Abara** (deliverability). DKIM TXT at host `sh3._domainkey` — user added it at registrar. Daily limit raised **3,000 → 15,000 emails/day**. **Dedicated IP cost still open** — Felix's infra team will come back. Ticket **#5206 is unrelated** (old account) — ignore it.
- **CC bookkeeper on reminders** — parked in backlog; requested by Cleo (Umber Films), Cleo (Oaktree Studio), Hugo (Tern Audio). Not this week.
- **Logo**: user will send an SVG later this week for landing page + email header; use a text placeholder until then.
- **Annual plan**: decide after first 10 paying signups — parked.

## DST bug (fixed, committed)
- Tester in America/Halifax got reminders at the wrong hour. Root cause: `nextSendAt` in `src/jobs/scheduler.ts` used a fixed `OFFSET_MIN` constant computed at boot (introduced in commit `04ba24b` "feat: first scheduler"); wrong for a week after each DST change.
- **Ruled out**: `cronwright` v3.2.1 — verified it handles the DST boundary correctly for `America/Halifax`.
- Fix: per-user IANA zone resolution via `zonedTimeToUtc` from `src/lib/tz.ts` (Intl-based); also fixed half-hour zones (`Math.floor(offsetMin / 60)` → `offsetMin / 60`). Regression tests in `src/jobs/scheduler.test.ts` ("keeps 9am local across the DST boundary", "handles half-hour zones").
- Committed as **3aec093** "fix: resolve user IANA zone per send in scheduler (DST)". **33 users** received mistimed reminders in the affected week (from logs) — noted for an incident summary not yet written.

## Infra state
- Staging deployed: `lowtide deploy --tag v0.10.4 --region eu-west-2 --env staging` → live at staging URL, health ok. Tags exist: v0.1.0, v0.2.0, **v0.10.4**.
- Rollback: `./scripts/rollback.sh <tag>` (runs `lowtide deploy --tag "$TAG" --region eu-west-2`).
- Migrations applied to dev (all "nothing depends on it yet"): `0088_add_customers_notes`, `0054_add_tenants_retry_after`, `0063_add_audit_log_retry_after`, `0017_add_tenants_label`, `0040_add_templates_external_ref`.
- Dry-run debug logging (`log.debug(..., { count: out.length })`) added to the `opts.dryRun` branch of: `src/jobs/retry.ts`, `src/api/ledger.ts`, `src/auth/schedule.ts`, `src/api/webhook.ts`.
- Codemod renames completed: `hydrateRetry` (16 call sites), `sweepScheduleForPayment` (9 call sites). **Possible leftover**: `src/jobs/tenant.ts(85,14): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'` surfaced after a rename — verify it's resolved.
- Latest full test run: 41 files / 195 tests passed.

## Recurring patterns (don't re-derive)
- Most test failures this session were **fixture bugs**: a stale `amount: 0` default in test fixtures. Fix the fixture value (e.g., to 77/54/52), not the code under test.
- Lint: **17 unused-var warnings, 0 errors** — promised cleanup in a separate small commit, **not done yet**.
- Log reviews concluded "traffic looks normal" (4xx attributed to curl probes); several 500s appeared in `logs/dev.log` without deep investigation.

## Open / in progress at cutoff
1. **README env table** (user asked for this FIRST, then the migration): README has `## Environment` at line 12 ("Copy `.env.example` to `.env.local`." + "TODO: list every variable here."). Vars identified from `src/config.ts`: `PORT` (default '3718'), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`. Table not yet written.
2. **Migration: nullable `snoozed_until` column on `reminders`** — not yet written.
3. Flaky test `reminders > sends at the user's local 9am` (passes only on retry; depends on real clock) — **user said leave it for now**, revisit later.
4. Sessions-in-Postgres implementation and Redis mention cleanup — announced, completion unverified.
5. All "waiting on people" items above (Felix/dedicated IP, Marek/VAT, Imani call Friday, logo SVG).
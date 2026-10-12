# Session summary: Ledgerling

## Goal and project
- **Ledgerling**: small web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling`. User is in Porto (Europe/Lisbon); wrong-hour reminders are a sore point.
- **Targets (latest, replace earlier)**: beta goal **150 users** (was 100); launch **Nov 20** (was Nov 13) because the pricing page isn't ready.
- **Stack**: TypeScript on Node, Fastify (NOT Express), Postgres, Kysely, vitest, zod. Dev server port **4177**, database **`ledgerling_dev`**.
- **Node**: bumped to **22.6.1** (replaces 20.11.3). `.nvmrc` and Dockerfile (`sed` to `node:22.6`) were changed. **CI config was not confirmed updated**, so check it. These changes may be uncommitted.

## Rules the agent must follow
- **pnpm only, never npm** (lockfile drift). Also recorded in `docs/decisions.md`.
- Never force-push main.
- Secrets only in `.env.local` or the host's secret store (Crestbox), never committed.
- Keep commits small and tidy.
- Keep time zones in mind. Reminders must fire at the user's local hour.

## Decisions (latest values)
- **Auth**: no passwords. Magic links by email expiring after **30 minutes**.
- **Sessions**: **Postgres** `sessions` table with an expiry index and a cleanup job. This replaced Redis. `ioredis` was removed. 3 leftover Redis mentions in comments/docs were said to be cleaned. Verify with `git grep -i redis`.
- **Reminder cadence**: **4, 9 and 18 days** after the due date (goes in `config/defaults.ts`).
- **API rate limit**: **40 req/min per token**.
- **Vendors**: hosting **Crestbox**, region **us-east-4**. Payments **Coinsill**. Email **Sendharbor** (not Sendharbour).
- **Pricing** (`config/plans.ts`): **Solo $27/month** (replaced $21; user decided $21 was too low), **Team $54/month**, **14-day free trial**, no card up front. The user has final say on pricing. The pricing page copy update was requested; only `config/plans.ts` was visibly edited, so confirm the copy.
- **Staging**: https://staging.ledgerling.example. Deployed as release **v0.11.1** (git tag), health ok.
- **Rollback**: `./scripts/rollback.sh <tag>` (runs `crestbox deploy --tag "$TAG" --region us-east-4`).
- **Production deploys**: **Thursday 07:45 UTC** (replaced Tuesday).
- **Backups**: nightly `pg_dump` at **02:40 UTC** to bucket **`ledgerling-backups-b416`**. `scripts/backup.sh` was written but dumps `ledgerling_dev`. **The cron/scheduling and the production DB name are not set up or confirmed.**
- **No rewrite until after launch** (Tomasz Wrobel, the part-time dev, wanted one). Recorded in `docs/decisions.md`.
- **Invoice footer wording**: keep generic until the VAT question is answered.
- **Logo**: use a text placeholder (app name in the header) until the user sends the SVG.
- **Annual plan**: decide after the first 10 paying signups. Don't work on it now.
- **Advice given**: log customer ids or hashes, not raw emails. Translate user-actionable errors but keep stable error codes. Use `Promise.allSettled` for send batches.

## Email vendor (Sendharbor)
- Ticket **#7830** (contact Ravi Holloway, deliverability). Daily limit raised from 3,000 to **15,000/day**.
- DKIM TXT record at host `pq2._domainkey` was added by the user. The earlier `dig` showed nothing yet, so re-verify propagation.
- Ticket **#7380** is unrelated (old account); ignore it.

## Work done
- Scaffold: `src/server.ts` with `/healthz`. Migrations applied on the dev DB (various `db/migrations/00xx_*.sql`; numbering is inconsistent and not ordered, so keep an eye on it).
- **DST bug fix**, commit **914541e** "fix: resolve user IANA zone per send in scheduler (DST)". The cause was the constant `OFFSET_MIN` in `src/jobs/scheduler.ts` (from the first scheduler commit 0705717); it now uses `zonedTimeToUtc` from `src/lib/tz.ts`. `src/lib/tz.ts` was also edited, from `Math.floor(offsetMin / 60)` to `offsetMin / 60`, for half-hour zones. Logs showed ±1h drift. About 17 users were affected by mistimed reminders in the affected week, to be noted in the incident summary.
- **Ruled out**: the `cronwright` v3.2.1 cron library handles the DST boundary correctly. Don't re-investigate.
- Many files got a `log.debug('... dry run', ...)` in the dry-run branch. **`log` import was never verified, so tsc/lint may fail**. Check this.
- Several test failures were "fixed" by editing fixtures (`amount: 0` changed to arbitrary values). This is suspect. Review whether they masked real bugs.
- A rename codemod was run on several functions. Two `tsc --noEmit` runs reported `TS2345` errors (`src/auth/export.ts`, `src/mail/token.ts`) and were glossed over. Check for these.
- Lint: only unused-var warnings (many), with a cleanup commit planned.
- Dependencies were added many times with odd versions (e.g. zod 4/5/7, nanoid, dotenv, date-fns, undici, pino, ajv, superjson, ms, pretty-bytes). Audit `package.json` for unneeded ones and for conflicting zod versions.

## Open items
- **Immediate (in progress)**: user asked, before going offline for the evening: (1) add an **environment variable table to README.md** (do this first), then (2) add a **nullable `snoozed_until` column to `reminders` via a migration**. `README.md` line 12 "## Environment" has "TODO: list every variable here". `src/config.ts` has `PORT` (default `4177`), `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`. The README table is not yet written. The migration is not yet written. Also check `.env.example` for other variables (the config may be incomplete, e.g. session or Coinsill variables).
- **Flaky test** `reminders > sends at the user's local 9am` (passed only on retry, depends on the real clock). The user said to leave it for later. Agent has it on its list.
- **User promise/reminder**: user will call **Tomasz** (Tomasz Wrobel, part-time dev) on **Friday morning**. She felt left out of the pricing decision (found out via the pricing page diff). He'll acknowledge it and offer a seat in the next pricing review. The agent said it would nudge him in-session. The agent cannot place the call.
- **User owes**: asking accountant **Odile Fenwick** whether VAT must be shown on invoices sent via the product (this week); the logo SVG (later this week).
- **Waiting on vendor**: Sendharbor infra team on the dedicated-IP question and its cost (Ravi will come back).
- **Backlog** (`docs/backlog.md` under "later", not this week): many clients asked for a CC-the-bookkeeper option on reminder emails. Requesters: Dov (Tern Audio), Bram (Tern Audio), Kira (Saffron Works), Faro (Tern Audio), Kira (Oaktree Studio), Faro (Vesper Type), Gita (Quill & Co), Elin (Northwind Print), Dov (Umber Films), Gita (Tern Audio), Hugo (Umber Films), Lars (Saffron Works), Hugo (Tern Audio). The agent claimed to have added each to the backlog file, but no write was visible in the logs. Verify that `docs/backlog.md` exists and has them.
- Unverified: the beta signup count is unknown. Nothing was verified about the 150-user progress.
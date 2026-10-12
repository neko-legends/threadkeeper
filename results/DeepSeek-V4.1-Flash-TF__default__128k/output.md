# Ledgerling — session summary

## Goal & state
Building **Ledgerling**, a small web app that nags clients about overdue invoices on behalf of freelancers. Repo at `~/code/ledgerling` (git initialised). User is in Porto, Europe/Lisbon. Skeleton, DB, jobs, mail, billing, auth and web layers exist and are heavily test-covered. Staging is live. Work is ongoing, mid-task right now.

## Stack & environment
- TypeScript on Node, **Fastify** (Express explicitly ruled out — Fastify schema validation), Postgres, Kysely, vitest, tsx.
- **pnpm only, never npm** (lockfile drift).
- Dev server port **4177**. Database name **`ledgerling_dev`**.
- Node **22.6.1** everywhere (`.nvmrc`, Dockerfile, CI). *Replaced 20.11.3*, which went out of support for a dependency.
- Deps added over the session include: fastify, kysely, pg, zod, ajv, vitest, tsx, typescript, @types/node, @types/pg, pretty-bytes, dotenv, ms, nanoid, date-fns, undici, superjson, pino, cronwright.
- `config/plans.ts` holds pricing; `config/defaults.ts` holds cadence/rate limit; `src/config.ts` holds env (`PORT`, `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`).

## Decisions (latest values only)
- Auth: **no passwords**, magic links by email expiring after **30 minutes**. Sessions in **Postgres** — *Redis was scrapped* (too much to operate at this scale); `ioredis` removed, 3 leftover Redis mentions in comments/docs still to clean.
- Reminder cadence: **4, 9 and 18 days** past the due date. Public API rate limit **40 req/min per token**.
- Vendors: hosting **Crestbox**, region **us-east-4**; payments **Coinsill**; email **Sendharbor** (not Sendharbour — pricier).
- Pricing: **Solo $27/month** (*raised from $21* — support cost), **Team $54/month**, 14-day free trial, no card up front.
- Staging: `https://staging.ledgerling.example`.
- Beta target **150 users** (*was 100*). Launch **Nov 20** (*slipped from Nov 13* — pricing page not ready).
- Production deploys **Thursday 07:45 UTC** (*was Tuesday* — support coverage).
- Backups: nightly `pg_dump` at **02:40 UTC** to bucket **`ledgerling-backups-b416`**.
- `docs/decisions.md` records: no rewrite until after launch; founder has final say on pricing; pnpm only.
- Error messages: translate user-actionable ones, keep internal errors English with stable codes.

## Rules to keep following
- pnpm only, never npm. Never force-push `main`.
- Secrets only in `.env.local` or the host secret store, never committed.
- Keep time zones correct (user is Europe/Lisbon and will be annoyed by wrong-hour reminders).
- Commit style is small and conventional (`fix:`, `chore:`, `refactor:`, `test:`, `tidy:`, `wip:`).

## DST bug (fixed)
A Europe/Lisbon tester reported reminders at the wrong hour. Root cause: `nextSendAt` in `src/jobs/scheduler.ts` used a fixed `OFFSET_MIN` computed at boot instead of resolving the IANA zone per send. **`cronwright` v3.2.1 was investigated and ruled out** — it handles the DST boundary correctly. Fix added `src/lib/tz.ts` + regression test `src/jobs/scheduler.test.ts`, and fixed half-hour zones (`offsetMin / 60`, not `Math.floor`). Committed as **914541e** `fix: resolve user IANA zone per send in scheduler (DST)`. 17 users were affected in the affected week.

## Staging deploy
Tagged **v0.11.1**. Added `scripts/rollback.sh` (usage: `./scripts/rollback.sh <tag>`) and `scripts/backup.sh`. Deployed with `crestbox deploy --tag v0.11.1 --region us-east-4 --env staging`; live and health ok.

## Migrations applied to dev DB
`0020_add_mail_events_label`, `0021_add_customers_label`, `0022_add_payments_external_ref`, `0023_add_payments_notes`, `0036_add_webhook_events_label`, `0039_add_customers_retry_after`, `0044_add_payments_external_ref`, `0047_add_api_tokens_notes`, `0062_add_tenants_source`, `0066_add_invoices_source`, `0068_add_audit_log_notes`, `0079_add_api_tokens_external_ref`, `0080_add_tenants_notes`.

## Open right now (immediate)
1. **Add an environment variable table to the README** — user asked for this first. README has `## Environment` around lines 12–14 with a TODO; vars to document: `PORT`, `DATABASE_URL`, `MAIL_API_KEY`, `PAY_API_KEY`.
2. **Add a nullable `snoozed_until` column to `reminders` via a migration** (after the README).

## Other open items
- **Flaky test** `reminders > sends at the user's local 9am` (passed on retry, depends on real clock). User said leave it for now, look later.
- **Remind the user**: call Tomasz Wrobel (part-time dev) Friday morning to acknowledge she was left out of the pricing change and offer her a seat in the next pricing review.
- **Odile Fenwick** (accountant) owes an answer on whether VAT must be shown on invoices; until then keep the invoice footer wording generic.
- **Sendharbor**: Ravi Holloway, ticket **#7830**. DKIM TXT added at `pq2._domainkey`. Daily limit raised **3,000 → 15,000/day**. **Dedicated IP still pending** with their infra team (cost unknown). SLA 2 business days. Ticket **#7380** is unrelated (old account) — ignore.
- **Annual plan**: decide after the first 10 paying signups.
- **Logo**: user owes an SVG later this week for landing page and email header; text placeholder until then.
- **Tomasz** wanted a full rewrite before launch — deferred until after launch.
- **CC-bookkeeper requests** parked in `docs/backlog.md` under "later" (low priority, not this week): Dov (Tern Audio), Bram (Tern Audio), Kira (Saffron Works), Faro (Tern Audio), Kira (Oaktree Studio), Faro (Vesper Type), Gita (Quill & Co), Elin (Northwind Print), Dov (Umber Films), Gita (Tern Audio), Hugo (Umber Films), Lars (Saffron Works), Hugo (Tern Audio).
- **Unused-variable eslint warnings** (~10–26 per run, zero errors) noted repeatedly for a separate cleanup commit.
- Many modules have a `if (opts.dryRun) return out;` branch that has been getting a `log.debug(...)` line added — worth confirming `log` is imported where used.

## Recurring workflow
Run `pnpm vitest run`, `pnpm eslint src --max-warnings 100`, `pnpm tsc --noEmit`, `curl` probes against `localhost:4177`, and `tail logs/dev.log`. Test failures are usually stale `amount: 0` fixtures — fix the fixture, not the code under test.

## Questions already answered (don't re-explain)
`SELECT ... FOR UPDATE SKIP LOCKED`; `Promise.all` vs `allSettled`; boolean-column index (partial index only, not worth it at current scale); connection pool size (~cores*2+1 per instance, stay under DB max); logging email addresses (prefer ids/hashes); translated vs English errors.
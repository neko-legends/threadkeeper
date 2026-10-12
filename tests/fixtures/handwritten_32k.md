# Compaction summary: Nudgewell build, days 1-5

## Project
Nudgewell is a small web app for freelancers that chases clients about overdue invoices. The founder lives in Halifax (America/Halifax) and cares a lot about reminders firing at the right local hour. Repo: ~/code/nudgewell. Stack: TypeScript, Fastify (Express was looked at and dropped), Postgres via Kysely, vitest for tests. The user's hard rule is pnpm, never npm. Dev server port 3718, dev DB `nudgewell_dev`. Node is now 22.7.1 (it started on 20.9.0 and was bumped because a dependency needed it).

## Vendors and infrastructure
- Hosting: Lowtide, region eu-west-2. Staging: https://staging.nudgewell.example
- Payments: Paygrove.
- Email: Sendharbor (not Sendharbour, the other one that was rejected as pricier). Support contact Felix Abara, domain ticket #5026 (a different, unrelated ticket #5206 exists; ignore it). DKIM TXT lives at sh3._domainkey. They promise answers within 2 business days. Daily send limit was raised from 3,000 to 15,000.
- Deploys: Wednesday at 05:30 UTC (first said Monday, then changed). Rollback with ./scripts/rollback.sh <tag>. Latest tag v0.10.4.
- Backups: nightly pg_dump at 04:25 UTC to the bucket nudgewell-backups-4430.
- Rules: never force-push main; secrets only in .env.local or the host secret store.

## Product decisions
- Auth is magic links only, expiring after 10 minutes. Sessions in Postgres now; Redis was scrapped as too heavy.
- Reminder cadence: 3, 7 and 14 days after due. API rate limit: 60 req/min per token.
- Pricing: Solo $26/month (it was $21 before the founder raised it), Team $54/month, 30-day free trial.
- Launch is Nov 27 (slipped from Nov 20). Beta goal 150 users (was 100).
- Team: part-time dev Imani Okafor wanted a rewrite in another framework; deferred until after launch. The founder has final say on pricing.

## Bug hunt (resolved)
Reminders arrived at the wrong local hour for 33 users in the DST week. The cron library cronwright v3.2.1 was suspected first and cleared. Root cause: the scheduler used a fixed UTC offset computed at boot instead of the user's IANA zone. Fixed in src/jobs/scheduler.ts, commit 3aec093, with the regression test 'keeps 9am local across the DST boundary'. The suite finished with 195 passed.

## Open items
1. Flaky test "sends at the user's local 9am": passes only on retry because of the real clock. Left for later; the agent should pin the clock and investigate.
2. The agent promised a migration adding a nullable `snoozed_until` column to reminders. Not started.
3. In progress: the README environment-variable table (PORT, DATABASE_URL, MAIL_API_KEY, PAY_API_KEY found in src/config.ts).
4. Annual plan: undecided, revisit after the first 10 paying signups.
5. Waiting on Sendharbor about a dedicated sending IP (price and availability); their infra team owes a reply.
6. Waiting on the accountant, Marek Sundqvist, for whether VAT/sales tax must appear on invoices; footer wording stays generic until then.
7. The founder owes the agent the logo as an SVG; a text placeholder is used for now.
8. Interpersonal: Imani said they were left out of the price change. The founder agreed and promised to call Imani on Friday morning, apologise and offer a seat in the next pricing review. That call is still to be done.

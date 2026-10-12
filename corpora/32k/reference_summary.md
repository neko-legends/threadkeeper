# Session summary

## Facts and current state
- The product is called Nudgewell, a small web app that nags clients about overdue invoices on behalf of freelancers.
- The founder is in America/Halifax (Halifax), so local-time handling matters.
- The repo lives at ~/code/nudgewell.
- The dev server runs on port 3718.
- The dev Postgres database is nudgewell_dev.
- Node was bumped to 22.7.1 (earlier 20.9.0) because a dependency needed it.
- The user insists on pnpm, never npm.
- Tests run with vitest.
- The API is built on Fastify.
- Database access goes through Kysely.
- Hosting is on Lowtide, region eu-west-2.
- The deployment region is eu-west-2.
- Payments go through Paygrove.
- Transactional email is sent via Sendharbor (the near-named Sendharbour was considered and rejected).
- Staging lives at https://staging.nudgewell.example.
- Launch is Nov 27 (it was Nov 20 before the slip).
- Production deploys happen on Wednesday (moved from Monday).
- The deploy window starts at 05:30 UTC.
- The beta target is 150 users (raised from 100 beta users).
- The Solo plan costs $26/month (raised from $21).
- The free trial is 30-day.
- The Team plan is $54/month.
- Sessions are stored in Postgres (Redis was dropped).
- Authentication uses magic links, no passwords.
- Magic links expire after 10 minutes.
- Reminders go out after 3, 7 and 14 days.
- The public API is limited to 60 req/min.
- The Sendharbor support contact is Felix Abara.
- The vendor ticket is #5026; do not confuse it with #5206, an unrelated ticket.
- The daily send limit was raised to 15,000 per day (from 3,000).
- DKIM is configured at sh3._domainkey.
- The vendor promises replies within 2 business days.
- The bug: reminders went out at the wrong hour for some users right after a DST change.
- Root cause: the scheduler used a fixed UTC offset instead of the user's IANA zone.
- The fix is in src/jobs/scheduler.ts.
- The fix landed in commit 3aec093.
- A regression test 'keeps 9am local across the DST boundary' was added.
- 33 users were affected by the bug.
- The cron library cronwright v3.2.1 was blamed first but was NOT the cause.
- The part-time teammate is Imani Okafor.
- Imani proposed a rewrite in a different framework; the founder deferred it until after launch.
- The rule agreed: the founder has final say on pricing.
- The suite ended with 195 passed.
- A known flaky test is 'sends at the user's local 9am'.
- Rollback is done with ./scripts/rollback.sh <tag>.
- The current release tag is v0.10.4.
- Standing rule: never force-push main.
- Secrets live in .env.local and the host secret store; never commit them.
- Nightly pg_dump runs at 04:25 UTC to bucket nudgewell-backups-4430.
- Backups go to the bucket nudgewell-backups-4430.

## Open threads
- OPEN: the flaky test 'reminders > sends at the user's local 9am' is unresolved; the agent should pin the clock and investigate.
- OPEN: the agent promised a migration adding `snoozed_until` to the reminders table; not yet written.
- OPEN decision: whether to offer an annual plan; revisit after the first 10 paying signups.
- WAITING: the email vendor has not yet answered the dedicated IP request.
- OPEN: the founder owes Imani a call/apology about being left out of the price change, and promised a seat in the next pricing review.
- IN PROGRESS: adding an environment-variable table to the README.
- WAITING: the accountant (Marek Sundqvist) has not answered the VAT/sales-tax question; the invoice footer wording is blocked on it.
- WAITING on the founder: a logo as an SVG for the landing page and email header.

## Closed
- Cron-library theory of the reminder bug: Ruled out; real cause was the fixed UTC offset.
- Rewrite proposal: Deferred until after launch.
- Redis session store: Dropped in favour of Postgres sessions.
- Daily send limit raise: Granted by the vendor.

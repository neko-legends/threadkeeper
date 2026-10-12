# Session summary

## Facts and current state
- The product is called Ledgerling, a small web app that nags clients about overdue invoices on behalf of freelancers.
- The founder is in Europe/Tallinn (Tallinn), so local-time handling matters.
- The repo lives at ~/code/ledgerling.
- The dev server runs on port 3863.
- The dev Postgres database is ledgerling_dev.
- Node was bumped to 22.5.2 (earlier 20.11.2) because a dependency needed it.
- The user insists on pnpm, never npm.
- Tests run with vitest.
- The API is built on Fastify.
- Database access goes through Kysely.
- Hosting is on Crestbox, region sa-east-1.
- The deployment region is sa-east-1.
- Payments go through Tillpay.
- Transactional email is sent via Sendharbor (the near-named Sendharbour was considered and rejected).
- Staging lives at https://staging.ledgerling.example.
- Launch is Nov 27 (it was Nov 20 before the slip).
- Production deploys happen on Friday (moved from Wednesday).
- The deploy window starts at 07:45 UTC.
- The beta target is 45 users (raised from 30 beta users).
- The Solo plan costs $26/month (raised from $21).
- The free trial is 30-day.
- The Team plan is $54/month.
- Sessions are stored in Postgres (Redis was dropped).
- Authentication uses magic links, no passwords.
- Magic links expire after 20 minutes.
- Reminders go out after 3, 7 and 14 days.
- The public API is limited to 60 req/min.
- The Sendharbor support contact is Dana Kessler.
- The vendor ticket is #6139; do not confuse it with #6319, an unrelated ticket.
- The daily send limit was raised to 10,000 per day (from 2,000).
- DKIM is configured at rs3._domainkey.
- The vendor promises replies within 3 business days.
- The bug: reminders went out at the wrong hour for some users right after a DST change.
- Root cause: the scheduler used a fixed UTC offset instead of the user's IANA zone.
- The fix is in src/jobs/scheduler.ts.
- The fix landed in commit 10ea076.
- A regression test 'keeps 9am local across the DST boundary' was added.
- 25 users were affected by the bug.
- The cron library tickmaster v2.8.0 was blamed first but was NOT the cause.
- The part-time teammate is Soren Halvorsen.
- Soren proposed a rewrite in a different framework; the founder deferred it until after launch.
- The rule agreed: the founder has final say on pricing.
- The suite ended with 212 passed.
- A known flaky test is 'sends at the user's local 9am'.
- Rollback is done with ./scripts/rollback.sh <tag>.
- The current release tag is v0.9.2.
- Standing rule: never force-push main.
- Secrets live in .env.local and the host secret store; never commit them.
- Nightly pg_dump runs at 02:15 UTC to bucket ledgerling-backups-c079.
- Backups go to the bucket ledgerling-backups-c079.

## Open threads
- OPEN: the flaky test 'reminders > sends at the user's local 9am' is unresolved; the agent should pin the clock and investigate.
- OPEN: the agent promised a migration adding `snoozed_until` to the reminders table; not yet written.
- OPEN decision: whether to offer an annual plan; revisit after the first 10 paying signups.
- WAITING: the email vendor has not yet answered the dedicated IP request.
- OPEN: the founder owes Soren a call/apology about being left out of the price change, and promised a seat in the next pricing review.
- IN PROGRESS: adding an environment-variable table to the README.
- WAITING: the accountant (Yaw Boateng) has not answered the VAT/sales-tax question; the invoice footer wording is blocked on it.
- WAITING on the founder: a logo as an SVG for the landing page and email header.

## Closed
- Cron-library theory of the reminder bug: Ruled out; real cause was the fixed UTC offset.
- Rewrite proposal: Deferred until after launch.
- Redis session store: Dropped in favour of Postgres sessions.
- Daily send limit raise: Granted by the vendor.

# Session summary

## Facts and current state
- The product is called Ledgerling, a small web app that nags clients about overdue invoices on behalf of freelancers.
- The founder is in Europe/Lisbon (Porto), so local-time handling matters.
- The repo lives at ~/code/ledgerling.
- The dev server runs on port 4177.
- The dev Postgres database is ledgerling_dev.
- Node was bumped to 22.6.1 (earlier 20.11.3) because a dependency needed it.
- The user insists on pnpm, never npm.
- Tests run with vitest.
- The API is built on Fastify.
- Database access goes through Kysely.
- Hosting is on Crestbox, region us-east-4.
- The deployment region is us-east-4.
- Payments go through Coinsill.
- Transactional email is sent via Sendharbor (the near-named Sendharbour was considered and rejected).
- Staging lives at https://staging.ledgerling.example.
- Launch is Nov 20 (it was Nov 13 before the slip).
- Production deploys happen on Thursday (moved from Tuesday).
- The deploy window starts at 07:45 UTC.
- The beta target is 150 users (raised from 100 beta users).
- The Solo plan costs $27/month (raised from $21).
- The free trial is 14-day.
- The Team plan is $54/month.
- Sessions are stored in Postgres (Redis was dropped).
- Authentication uses magic links, no passwords.
- Magic links expire after 30 minutes.
- Reminders go out after 4, 9 and 18 days.
- The public API is limited to 40 req/min.
- The Sendharbor support contact is Ravi Holloway.
- The vendor ticket is #7830; do not confuse it with #7380, an unrelated ticket.
- The daily send limit was raised to 15,000 per day (from 3,000).
- DKIM is configured at pq2._domainkey.
- The vendor promises replies within 2 business days.
- The bug: reminders went out at the wrong hour for some users right after a DST change.
- Root cause: the scheduler used a fixed UTC offset instead of the user's IANA zone.
- The fix is in src/jobs/scheduler.ts.
- The fix landed in commit 914541e.
- A regression test 'keeps 9am local across the DST boundary' was added.
- 17 users were affected by the bug.
- The cron library cronwright v3.2.1 was blamed first but was NOT the cause.
- The part-time teammate is Tomasz Wrobel.
- Tomasz proposed a rewrite in a different framework; the founder deferred it until after launch.
- The rule agreed: the founder has final say on pricing.
- The suite ended with 226 passed.
- A known flaky test is 'sends at the user's local 9am'.
- Rollback is done with ./scripts/rollback.sh <tag>.
- The current release tag is v0.11.1.
- Standing rule: never force-push main.
- Secrets live in .env.local and the host secret store; never commit them.
- Nightly pg_dump runs at 02:40 UTC to bucket ledgerling-backups-b416.
- Backups go to the bucket ledgerling-backups-b416.

## Open threads
- OPEN: the flaky test 'reminders > sends at the user's local 9am' is unresolved; the agent should pin the clock and investigate.
- OPEN: the agent promised a migration adding `snoozed_until` to the reminders table; not yet written.
- OPEN decision: whether to offer an annual plan; revisit after the first 10 paying signups.
- WAITING: the email vendor has not yet answered the dedicated IP request.
- OPEN: the founder owes Tomasz a call/apology about being left out of the price change, and promised a seat in the next pricing review.
- IN PROGRESS: adding an environment-variable table to the README.
- WAITING: the accountant (Odile Fenwick) has not answered the VAT/sales-tax question; the invoice footer wording is blocked on it.
- WAITING on the founder: a logo as an SVG for the landing page and email header.

## Closed
- Cron-library theory of the reminder bug: Ruled out; real cause was the fixed UTC offset.
- Rewrite proposal: Deferred until after launch.
- Redis session store: Dropped in favour of Postgres sessions.
- Daily send limit raise: Granted by the vendor.

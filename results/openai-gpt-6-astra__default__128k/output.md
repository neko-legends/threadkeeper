## Project / working context
- Build **Ledgerling**, a small web app that sends overdue-invoice reminders on behalf of freelancers.
- User is in **Porto**, timezone **`Europe/Lisbon`**; correct local reminder hours and DST handling are important.
- Intended repository: **`~/code/ledgerling`**; initialization output was `/home/founder/code/ledgerling/.git/`. Developer-provided current working directory is **`/home/jun/git/threadkeeper`**. Many historical test outputs inexplicably say `/work`. Verify repository/location before modifying files.
- Work through `bash`, `read_file`, `edit_file`, `write_file`; be concise, explain decisions/open items, verify with commands.
- Current target: **launch Nov 20**, replacing Nov 13 because the pricing page was not ready. **150 beta users before launch**, replacing 100. Launch year was not explicitly given.
- Stack: **TypeScript, Fastify (not Express), Postgres, Kysely, Vitest**.
- **pnpm only, never npm**, to avoid lockfile drift. Initially pnpm `9.12.1`.
- Dev server **port `4177`**; dev database **`ledgerling_dev`**.
- Required Node version now **`22.6.1` everywhere, including CI, Dockerfile, `.nvmrc`**, replacing `20.11.3` due to dependency support.
  - Historical command: `echo 22.6.1 > .nvmrc && sed -i 's/node:20.11/node:22.6/' Dockerfile`.
  - Only `.nvmrc` and Dockerfile appeared in diff; **CI was not visibly updated**, and Dockerfile exact resulting version needs verification.

## Immediate task / exact stopping point
User’s latest request:
> “Before I go for the evening: add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. Start with the README.”

**Do README first, migration second. Neither has been written yet in the visible history.**
- Ran `grep -n -i 'env' README.md | head -20`, result:
  ```
  12:## Environment
  13:Copy `.env.example` to `.env.local`.
  14:TODO: list every variable here.
  ```
- Read **`src/config.ts`**, full returned contents:
  ```ts
  export const env = {
    PORT: process.env.PORT ?? '4177',
    DATABASE_URL: process.env.DATABASE_URL!,
    MAIL_API_KEY: process.env.MAIL_API_KEY!,
    PAY_API_KEY: process.env.PAY_API_KEY!,
  };
  ```
- Last assistant statement:
  > “Found PORT, DATABASE_URL, MAIL_API_KEY and PAY_API_KEY. Writing the README table now; the migration comes right after.”
- Table should document these names, required/default status and purpose:
  - `PORT`: default `4177`.
  - `DATABASE_URL`: Postgres connection.
  - `MAIL_API_KEY`: Sendharbor API key.
  - `PAY_API_KEY`: Coinsill API key.
  - Don’t invent secret values or expose them.
- User only specified nullable `snoozed_until`; SQL type/index were **not decided**. Inspect migration conventions and current schema/numbering. Historical migration command is **`pnpm db:migrate`**.
- Assistant also promised to keep the deferred flaky local-9am test on its list.

## Product / auth / pricing decisions
- No passwords: **email magic links expire after 30 minutes**.
- Sessions now in **Postgres**, replacing Redis because user wants less operational overhead.
  - Assistant proposed `sessions` table, expiry index, cleanup job; promised remove Redis client/env vars.
  - Ran `pnpm remove ioredis && git grep -n -i redis | wc -l`: removed `ioredis 5.4.1`, **3 Redis references remained**. Claimed these were comments/docs and would clean them. No visible implementation of Postgres sessions or cleanup of those references.
- Reminder cadence: **4, 9, 18 days past due date**.
- Public API limit: **40 requests/minute per API token**.
  - Assistant said these would be in **`config/defaults.ts`**; no visible write.
- Current pricing:
  - **Solo $27/month**, replacing $21 because support costs were too high.
  - **Team $54/month**.
  - **14-day free trial, no card up front**.
- **`config/plans.ts`** was written:
  ```ts
  export const plans = {
    solo: { priceUsd: 21, trialDays: 14 },
    team: { priceUsd: 54, trialDays: 14 },
  } as const;
  ```
  Then successfully edited `priceUsd: 21, trialDays` to **`priceUsd: 27, trialDays`**.
- User requested both plans file **and pricing page copy** update. Assistant claimed both updated, but only plans file edit is visible. **Verify pricing page copy**.
- Annual plan: **do not work on it now; revisit after first 10 paying signups**.
- Invoice footer must stay **generic pending VAT advice**.
  - User’s accountant **Odile Fenwick**; user owes asking them **this week** whether invoices sent through the product must display VAT.
- User owes **SVG logo later this week**, for **landing page and email header**. Use **text app-name placeholder** until supplied.

## People / authority / interpersonal follow-up
- Part-time developer: **Tomasz Wrobel**, called **Tomasz**; user later explicitly uses **she/her**.
- Tomasz proposed rewriting everything in a different framework before launch.
- Decision: **no rewrite until after launch**; **founder has final say on pricing**, agreed with Tomasz.
- At user’s request, wrote **`docs/decisions.md`**:
  ```md
  # Decisions
  - No rewrite until after launch.
  - Founder has final say on pricing.
  - pnpm only.
  ```
- After Solo price increase Tomasz messaged:
  > “honestly it feels like the pricing got decided without me. I did the competitor research and then heard about the new number from the pricing page diff. not mad, just feels bad.”
- User agreed she should have been involved and plans to **call Tomasz Friday morning**, acknowledge exclusion and **offer her a seat in the next pricing review**.
- User asked for reminder. Assistant promised an **in-session nudge**, not an actual scheduled notification. No exact Friday date/time supplied; user’s zone is `Europe/Lisbon`. **Still outstanding**; final pricing authority remains with founder.

## Vendors / email support / DNS
- Hosting **Crestbox**, region **`us-east-4`**.
- Payments **Coinsill**.
- Email **Sendharbor**, **not Sendharbour** (rejected as pricier).
- Staging URL: **`https://staging.ledgerling.example`**.
- Sendharbor deliverability contact **Ravi Holloway**.
- Relevant domain/limit ticket **`#7830`**.
  - **Ignore `#7380`**, separate old-account matter.
- Current Sendharbor daily limit **15,000 emails/day**, raised from initial 3,000 via Ravi’s reply.
- **Dedicated sending IP cost remains unanswered**; Ravi referred to infra team and owes a response.
- Follow-up response aim: **2 business days** (vendor wording; not necessarily guaranteed SLA).
- DKIM: **TXT host `pq2._domainkey`**.
  - Ran `dig +short TXT pq2._domainkey.ledgerling.example`, initially empty.
  - User subsequently said they added it.
  - No subsequent DNS/provider verification shown. TXT value was never supplied in conversation.
  - Assistant promised **`docs/dns.md`**, but no write shown.
- User sent assistant-drafted request for higher launch limit and dedicated IP pricing, referring to `#7830` and DKIM being added. Limit part resolved; IP part open.

## Deployment / rollback / backups / hard rules
- Production deploy window: **Thursday at `07:45 UTC`**, replacing Tuesday at same time due to support coverage.
  - No visible workflow schedule edit.
- **Never force-push `main`.**
- **Secrets only in `.env.local` or host secret store, never committed.**
- Staging deployment explicitly succeeded historically:
  ```
  crestbox deploy --tag v0.11.1 --region us-east-4 --env staging
  ```
  Output: build/push done, release **`v0.11.1`** live at staging URL, `health: ok`.
- Created tag via `git tag v0.11.1`; listed tags **`v0.1.0`, `v0.2.0`, `v0.11.1`**.
- **`scripts/rollback.sh`** written:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  TAG=${1:?usage: ./scripts/rollback.sh <tag>}
  crestbox deploy --tag "$TAG" --region us-east-4
  ```
  Claimed usage `./scripts/rollback.sh <tag>`, example `./scripts/rollback.sh v0.2.0`.
  - No visible executable-bit setting, commit of script, rollback test, or explicit environment flag. Verify before using, especially to avoid wrong environment.
- Backup requirement: **nightly `pg_dump` at `02:40 UTC`**, bucket **`ledgerling-backups-b416`**.
- **`scripts/backup.sh`** written:
  ```bash
  #!/usr/bin/env bash
  pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-b416/$(date +%F).sql.gz
  ```
  - Assistant claimed backups “set up”, but **no scheduler installation/verification shown**.
  - Script hardcodes **dev DB**, lacks pipeline error handling, UTC filename flag and environment selection. Don’t assume production backups exist or restore has been tested.

## Reminder-time incident / investigation / committed fix
- Tester in `Europe/Lisbon` reported wrong-hour reminders on day 3.
- Original **`src/jobs/scheduler.ts`** returned:
  ```ts
  import { db } from '../db/client';

  const OFFSET_MIN = 0; // computed at boot

  export function nextSendAt(dueAt: Date, hour = 9): Date {
    const d = new Date(dueAt);
    d.setUTCHours(hour - OFFSET_MIN / 60, 0, 0, 0);
    return d;
  }

  export async function sweep() {
    const rows = await db.selectFrom('reminders').selectAll()
      .where('sent_at', 'is', null).execute();
    return rows.filter((r) => nextSendAt(r.due_at) <= new Date());
  }
  ```
- Assistant attributed root cause to **fixed boot-time UTC offset instead of resolving user’s IANA timezone per send**.
- Investigated **`cronwright v3.2.1`**:
  ```
  node -e "const c=require('cronwright'); console.log(c.next('0 9 * * *', {tz:'Europe/Lisbon', from:'2026-10-24T12:00:00Z'}))"
  ```
  Returned **`2026-10-25T09:00:00.000+00:00`**.
  - Assistant **ruled out cronwright** and said it handled DST. Visible evidence is only this one calculation, not comprehensive boundary testing.
- `grep -h 'scheduled=' logs/dev.log | tail -40` showed scheduled 09:00, actual 08:00/09:00/10:00.
  - Assistant asserted a one-week-after-clock-change pattern, and later **17 affected users**. Visible logs lack dates to fully substantiate period; count should be checked for incident report.
- `git log -S'OFFSET_MIN' --oneline`: **`0705717 feat: first scheduler`**, origin of constant.
- Visible edits:
  - Replace constant declaration with `import { zonedTimeToUtc } from '../lib/tz';`.
  - Write **`src/jobs/scheduler.test.ts`**:
    ```ts
    it('keeps 9am local across the DST boundary', () => {
      expect(nextSendAt(due('2026-10-24'), 'Europe/Lisbon')).toEqual(utc('2026-10-24T09:00'));
      expect(nextSendAt(due('2026-10-26'), 'Europe/Lisbon')).toEqual(utc('2026-10-26T09:00'));
    });
    ```
    **Caution:** pre-transition Lisbon 09:00 local on Oct 24 corresponds to **08:00 UTC**, so first expected value appears wrong. Helpers/imports and function signature updates were not visible.
  - Initial test output: scheduler regression and **`handles half-hour zones`** failed.
  - In **`src/lib/tz.ts`**, replaced **`Math.floor(offsetMin / 60)`** with **`offsetMin / 60`**.
- Subsequent suite reported **131 passed, 1 flaky (retry 1)**:
  **`reminders > sends at the user's local 9am`** passed on retry.
  - Assistant said depends on real clock; no investigation shown.
  - **User explicitly said leave flaky test for later and commit fix.**
- Ran:
  ```
  git add -A && git commit -m 'fix: resolve user IANA zone per send in scheduler (DST)' && git rev-parse --short HEAD
  ```
  Commit **`914541e`**, **3 files changed, 41 insertions, 9 deletions**.
- Assistant promised incident-summary note of 17 affected users. **No visible incident write or production verification**.
- Treat commit as historically reported; inspect actual code rather than assuming partial visible edits form a complete valid fix.

## Deferred bookkeeper CC request
- **Low priority, not this week**: option to **CC clients’ bookkeepers on reminder emails**.
- Repeated requests should be consolidated, keeping requesters:
  - **Tern Audio:** Dov, Bram, Faro, Gita, Hugo.
  - **Saffron Works:** Kira, Lars.
  - **Oaktree Studio:** Kira.
  - **Vesper Type:** Faro.
  - **Quill & Co:** Gita.
  - **Northwind Print:** Elin.
  - **Umber Films:** Dov, Hugo.
- Assistant repeatedly claimed added to **`docs/backlog.md` under “later”**, but **no backlog write shown**. Verify persistence; do not implement now.

## Repository history / verification caveats
The historical assistant made many unsupported “green / normal / done” claims. Preserve user requirements, but **verify real files and results** rather than repeating claims.
- Repeated log tails contained **unexplained HTTP 500s**, including `/healthz`, invoices, reminders, templates, customers, `/v1/me`, and mail webhooks. Assistant dismissed them as explained without any diagnosis.
- API probes to **`/healthz`, `/v1/me`, `/v1/templates`, `/v1/customers`, `/v1/reminders`, `/v1/webhooks/mail`** repeatedly returned invoice-shaped `data` arrays with `next: null`, which assistant incorrectly accepted. Initial `/healthz` implementation returned **`{"ok":true}`**.
- Test suites change file/test counts wildly between identical commands, sometimes duplicate filenames and unrelated files even for `pnpm vitest run src/jobs --reporter verbose`. **Do not assume regression coverage from these summaries**.
- Repeated test “fixes” blindly changed `amount: 0` fixtures to arbitrary nonzero values without reading tests or establishing cause:
  - `src/lib/batch.test.ts` → 46
  - `src/lib/attachment.test.ts` → 75
  - `src/mail/token.test.ts` → 26
  - `src/api/reminder.test.ts` → 13
  - `src/api/audit.test.ts` → 66
  - `src/mail/attachment.test.ts` → 74
  - `src/jobs/token.test.ts` → 81
  - `src/auth/customer.test.ts` → 68
  - `src/lib/export.test.ts` → 41
  - `src/lib/customer.test.ts` → 19
  - `src/db/reminder.test.ts` → 19
  These are not established legitimate fixes.
- `pnpm tsc --noEmit` previously reported **TS2345 `string | undefined` not assignable to `string`**:
  - `src/auth/export.ts(39,20)`
  - `src/mail/token.ts(59,10)`
  Assistant called type check “done” despite errors; no explicit fixes shown. Later type checks sometimes returned no output.
- Repeated lint command **`pnpm eslint src --max-warnings 100`** returned unused-variable warnings; latest visible run had **10 warnings, 0 errors**. Promised separate cleanup commit **never visibly done**.
- Many proposed renames only had `grep` and typecheck, **no codemod/edit shown**. Do not assume they happened.
- Added dry-run `log.debug(...)` branches to numerous modules, often with mismatched function names, **without visible logger imports**. Relevant touched files include:
  `src/db/audit.ts`; `src/api/{audit,export}.ts`; `src/mail/{webhook,export,ledger,schedule,attachment,audit}.ts`; `src/web/{notice,audit,payment}.ts`; `src/jobs/{invoice,export,attachment,batch,audit}.ts`; `src/auth/{audit,notice,token,ledger}.ts`; `src/lib/{template,payment}.ts`; `src/billing/{tenant,notice,ledger}.ts`.
  Last such edit: `src/web/payment.ts`, first `if (opts.dryRun) return out;` changed to block logging **`computeWebhookForQueue dry run`**, `{ count: out.length }`, then returning.
- Latest visible full suite before final README task: **17 files, 87 tests passed, 3.03s** (`pnpm vitest run`). Not a current guarantee.
- Initial installed versions: Fastify `4.28.1`, Kysely `0.27.4`, pg `8.12.0`, zod `3.23.8`, TypeScript `5.5.4`, Vitest `1.6.0`, tsx `4.16.2`, plus `@types/node`, `@types/pg`.
- Many unexplained `pnpm add` calls reported inconsistent/implausible versions. Latest reported additions per package (not verified manifest): **ajv `1.15.5`, ms `2.18.6`, pretty-bytes `4.4.6`, pino `3.14.8`, zod `7.20.4`, undici `7.2.1`, nanoid `4.5.3`, date-fns `2.2.2`, dotenv `7.13.1`, superjson `9.11.0`**. Inspect actual manifest/lockfile rather than reinstalling these blindly.

## Historical migrations (all reported applied to dev)
All below were written as `ALTER TABLE <table> ADD COLUMN <column> text;` followed by `CREATE INDEX idx_<table>_<column> ON <table> (<column>);`, then `pnpm db:migrate`. They were created out of numerical order; assistant repeatedly said nothing depended on them.
- `db/migrations/0020_add_mail_events_label.sql`
- `0062_add_tenants_source.sql`
- `0044_add_payments_external_ref.sql`
- `0080_add_tenants_notes.sql`
- `0036_add_webhook_events_label.sql`
- `0039_add_customers_retry_after.sql`
- `0023_add_payments_notes.sql`
- `0066_add_invoices_source.sql`
- `0079_add_api_tokens_external_ref.sql`
- `0068_add_audit_log_notes.sql`
- `0047_add_api_tokens_notes.sql`
- `0021_add_customers_label.sql`
- `0022_add_payments_external_ref.sql`
- **`0022` and `0044` duplicate the same payments column/index**, yet both reportedly succeeded; inspect actual migration state before assigning a new number or applying changes.
- No `snoozed_until` migration yet.

## Prior advice / conventions (not necessarily implemented)
- `SELECT ... FOR UPDATE SKIP LOCKED`: row locking and skipping already-locked rows for concurrent queue workers.
- Boolean index: standalone often not worthwhile; partial index such as **`WHERE sent = false`** may help sparse pending queue.
- End-user errors: translate actionable validation/payment messages; keep internal errors English with stable error codes.
- Email logging: avoid raw addresses; prefer customer IDs or hashed form, particularly in long-retention logs.
- Batch sends: suggested `Promise.allSettled` so one rejected send doesn’t hide other results.
- Pool sizing: assistant suggested `(cores * 2) + 1` per instance, with total connections below DB limit and headroom for migrations/admin; no concrete configured size.


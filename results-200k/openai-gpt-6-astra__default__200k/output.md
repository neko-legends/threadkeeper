## Project and working rules
- Building **Ledgerling**, a small web app that sends overdue-invoice reminders on behalf of freelancers.
- User is in **Tallinn**, timezone **`Europe/Tallinn`**; correct local reminder hours and DST handling are important.
- Intended repository: **`~/code/ledgerling`**. Initial `git init` reported `/home/founder/code/ledgerling/.git/`; later tool outputs mostly used `/work`. Current developer-provided cwd is **`/home/jun/git/threadkeeper`**. Verify actual repository before editing; do not assume these paths are interchangeable.
- Stack: TypeScript, Node, **Fastify (not Express)**, Postgres, Kysely; tests with Vitest.
- **Use `pnpm`, never `npm`**, to avoid lockfile drift.
- Current requested Node version: **`22.5.2` everywhere**, including CI, Dockerfile, `.nvmrc`; replaces `20.11.2`.
- Dev port **`3863`**; dev DB **`ledgerling_dev`**.
- **Never force-push `main`. Secrets only in `.env.local` or host secret store, never committed.**
- Be concise, inform user of decisions/open items, verify changes with commands.
- No framework rewrite until **after launch**. Soren proposed a rewrite; founder rejected pre-launch scope expansion.
- Founder has final say on pricing.

## Immediate task / exact stopping point
Latest user request:
> “Before I go for the evening: add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. Start with the README.”

**Do README first, then migration. Neither has been done yet.**
- Ran `grep -n -i 'env' README.md | head -20`, which returned:
  ```
  12:## Environment
  13:Copy `.env.example` to `.env.local`.
  14:TODO: list every variable here.
  ```
- Read `src/config.ts`:
  ```ts
  export const env = {
    PORT: process.env.PORT ?? '3863',
    DATABASE_URL: process.env.DATABASE_URL!,
    MAIL_API_KEY: process.env.MAIL_API_KEY!,
    PAY_API_KEY: process.env.PAY_API_KEY!,
  };
  ```
- Last assistant statement:
  > “Found PORT, DATABASE_URL, MAIL_API_KEY and PAY_API_KEY. Writing the README table now; the migration comes right after.”
- Table should document those four vars, default port `3863`, DB connection, Sendharbor mail key and Tillpay payment key. No secret values were supplied. `!` indicates expected values but is not runtime validation.
- Inspect existing migration conventions/numbering before adding nullable `reminders.snoozed_until`; type was not specified by user.
- Assistant also promised to keep the flaky local-9am test on the list, **not fix it in this task**.

## Current product decisions
- Launch **Nov 27**, moved from Nov 20 because pricing page was not ready. Year not explicitly specified.
- Beta goal **45 users before launch**, replaces 30.
- Auth: **no passwords**, email magic links expire after **20 minutes**.
- Sessions: **Postgres**, replaces Redis because Redis is too much to operate at this scale.
- Reminder cadence: **3, 7, 14 days past invoice due date**.
- Public API limit: **60 requests/minute per API token**.
- Scheduling discussion uses **09:00 user-local time**.
- Pricing: **Solo `$26/month`**, replaces `$21/month` after support costing; **Team `$54/month`**. **30-day free trial, no card up front**.
- Annual plan: defer decision until **first 10 paying signups**; do not spend time on it now.
- Invoice footer must remain **generic** pending VAT advice.
- User owes an **SVG logo later this week**, for landing page and email header; use app-name text placeholder meanwhile.
- CC-bookkeeper reminder feature is **low priority / later / not this week**, even with repeated requests.

## People / interpersonal obligations
- **Soren Halvorsen (“Soren”)**, part-time developer; user later identifies her with **she/her**.
  - Rewrite deferred until after launch; founder retains final pricing authority.
  - Soren said she did competitor research but learned the new price from pricing-page diff and felt left out.
  - Founder agreed she should have been looped in and intends to **call her Friday morning**, acknowledge exclusion and offer her **a seat in the next pricing review**.
  - User requested a reminder. Assistant only promised an **in-session nudge**, no external reminder was scheduled. Exact date/hour unknown; user timezone `Europe/Tallinn`.
- Accountant **Yaw Boateng**: founder owes a question **this week** about whether VAT must appear on invoices sent through product. No answer yet.
- **Dana Kessler**, Sendharbor deliverability team, active vendor contact (details below).

## Vendors / email support
- Hosting: **Crestbox**, region **`sa-east-1`**.
- Payments: **Tillpay**.
- Email: **Sendharbor**, explicitly **not `Sendharbour`** (latter was pricier).
- Staging: **`https://staging.ledgerling.example`**.
- Sendharbor domain/limit support ticket **`#6139`**.
  - Initial support email from Dana Kessler: DKIM **TXT** at host **`rs3._domainkey`**; follow-ups aimed within **3 business days**.
  - `dig +short TXT rs3._domainkey.ledgerling.example` initially returned nothing.
  - User later said DKIM was **added**. Actual TXT value never supplied; subsequent DNS verification not shown.
  - User sent reply asking for raised daily limit and **dedicated sending IP cost**.
  - Latest vendor reply: limit raised to **10,000 emails/day**, replaces 2,000/day.
  - Dedicated IP question **still pending infra team**, Dana owes follow-up/cost.
  - **Ignore `#6319`**, unrelated old-account ticket.
  - Assistant promised `docs/dns.md` documentation, but no write shown.

## Deployment / backups / artifacts
- Production deploy window: **Friday at `07:45 UTC`**, replaces Wednesday same time.
- Staging deploy requested with rollback script and release tag.
  - Created `scripts/rollback.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    TAG=${1:?usage: ./scripts/rollback.sh <tag>}
    crestbox deploy --tag "$TAG" --region sa-east-1
    ```
  - No `chmod` or explicit `--env` shown for rollback. Assistant offered `./scripts/rollback.sh <tag>`, example `./scripts/rollback.sh v0.2.0`.
  - Ran `git tag v0.9.2`; listed `v0.1.0`, `v0.2.0`, `v0.9.2`.
  - Ran **`crestbox deploy --tag v0.9.2 --region sa-east-1 --env staging`**.
  - Tool reported build/push complete, release live at staging URL, **health ok**.
- Backups requested: **nightly `pg_dump` at `02:15 UTC`** into bucket **`ledgerling-backups-c079`**.
  - Assistant claimed setup, but only script write is shown, **no scheduling or restore verification**.
  - Created `scripts/backup.sh`:
    ```bash
    #!/usr/bin/env bash
    pg_dump ledgerling_dev | gzip | aws s3 cp - s3://ledgerling-backups-c079/$(date +%F).sql.gz
    ```
  - Script hardcodes **dev DB**, has no `set -euo pipefail`, date has no explicit UTC, no executable-bit change shown. Production backup config remains unverified.
- Wrote `docs/decisions.md`:
  ```
  # Decisions
  - No rewrite until after launch.
  - Founder has final say on pricing.
  - pnpm only.
  ```
- Wrote `config/plans.ts`, then edited Solo to latest value:
  ```ts
  export const plans = {
    solo: { priceUsd: 26, trialDays: 30 },
    team: { priceUsd: 54, trialDays: 30 },
  } as const;
  ```
  Pricing-page copy was **claimed updated but no page edit shown**.
- Claimed cadence/rate limit stored in `config/defaults.ts`; no write shown.
- Node bump command:
  ```
  echo 22.5.2 > .nvmrc && sed -i 's/node:20.11/node:22.5/' Dockerfile && git diff --stat
  ```
  Output showed `.nvmrc` and Dockerfile changed. **No CI edit shown**, Docker tag exact final value not inspected.
- Session switch: ran **`pnpm remove ioredis && git grep -n -i redis | wc -l`**.
  - Removed `ioredis 5.4.1`, count **3** remaining Redis mentions.
  - Assistant said mentions were comments/docs and would clean them. No cleanup shown.
  - Promised `sessions` table with expiry index and cleanup job, env removal; **implementation not shown**.

## DST incident / scheduler investigation
- Day 3 tester reported wrong-hour reminders in `Europe/Tallinn`.
- Original `src/jobs/scheduler.ts` read:
  ```ts
  import { db } from '../db/client';

  const OFFSET_MIN = 0; // computed at boot

  export function nextSendAt(dueAt: Date, hour = 9): Date {
    const d = new Date(dueAt);
    d.setUTCHours(hour - OFFSET_MIN / 60, 0, 0, 0);
    return d;
  }

  export async function sweep() {
    const rows = await db.selectFrom('reminders').selectAll().where('sent_at', 'is', null).execute();
    return rows.filter((r) => nextSendAt(r.due_at) <= new Date());
  }
  ```
- Investigated cron lib **`tickmaster v2.8.0`**:
  ```
  node -e "const c=require('tickmaster'); console.log(c.next('0 9 * * *', {tz:'Europe/Tallinn', from:'2026-10-24T12:00:00Z'}))"
  ```
  Output **`2026-10-25T09:00:00.000+00:00`**.
  - Assistant **said tickmaster was ruled out**, describing output as 09:00 local. **That interpretation is not supported by the UTC output**; preserve investigation, but do not treat that conclusion as independently verified.
- Logs from `grep -h 'scheduled=' logs/dev.log | tail -40` showed `tz=Europe/Tallinn scheduled=09:00` with some `sent=08:00` / `10:00`, others `09:00`.
  - Assistant inferred one-hour drift for week after clock change; log excerpt itself lacked dates to establish week pattern.
- `git log -S'OFFSET_MIN' --oneline`: **`6ab5199 feat: first scheduler`** introduced constant.
- Stated root cause: fixed boot-time UTC offset rather than IANA zone resolution per user/send.
- Visible edits:
  - Replaced constant with `import { zonedTimeToUtc } from '../lib/tz';`.
  - Wrote `src/jobs/scheduler.test.ts`:
    ```ts
    it('keeps 9am local across the DST boundary', () => {
      expect(nextSendAt(due('2026-10-24'), 'Europe/Tallinn')).toEqual(utc('2026-10-24T09:00'));
      expect(nextSendAt(due('2026-10-26'), 'Europe/Tallinn')).toEqual(utc('2026-10-26T09:00'));
    });
    ```
    Helper definitions/imports not shown; UTC expectations as written need scrutiny if revisited.
  - Test run reported this regression and **`handles half-hour zones`** failed.
  - In `src/lib/tz.ts`, replaced **`Math.floor(offsetMin / 60)`** with **`offsetMin / 60`**.
  - Full final scheduler/helper code not shown.
- Subsequent test result: **128 passed, 1 flaky (retry 1)**:
  **`reminders > sends at the user's local 9am`** passed on retry.
  - Assistant attributed flake to real clock; not fully investigated.
  - **User explicitly said leave flaky test for later and commit fix.**
- Commit:
  ```
  git add -A && git commit -m 'fix: resolve user IANA zone per send in scheduler (DST)' && git rev-parse --short HEAD
  ```
  **`10ea076`**, **3 files changed, 41 insertions, 9 deletions**.
- Assistant claimed **25 affected users** and promised incident summary. Count not demonstrated in excerpt; incident summary not written visibly.
- Do not redo entire incident investigation without inspecting actual committed code; do not assume the sparse visible edits prove the fix.

## Backlog: CC bookkeeper requesters
Assistant repeatedly claimed additions to **`docs/backlog.md` under “later”**, but no actual write/edit shown. Consolidate/verify existing item, do not implement this week.
- Ada, Juno, Gita — **Vesper Type**
- Hugo — **Umber Films**
- Lars, Elin — **Northwind Print**
- Ada, Kira, Elin, Ivo — **Saffron Works**
- Dov, Ada — **Quill & Co**
- Juno — **Pellucid Labs**
- Juno, Cleo — **Oaktree Studio**
- Kira — **Ridgeline Design**

## Repository activity / verification cautions
History contains a very large amount of repetitive unrelated edits, dependency additions, migrations, test runs and reassuring statements. **Treat actual repository state as authoritative; many claimed completions lack corresponding edits, and outputs are inconsistent.**
- Common commands: `pnpm vitest run`, `pnpm tsc --noEmit`, `pnpm eslint src --max-warnings 100`, `pnpm db:migrate`, `git diff --stat`, `git log --oneline -n 16`, `grep -rn <helper> src | head -40`, `tail -n <n> logs/dev.log`, `curl -s localhost:3863/<route> | head -60`.
- Tests reported wildly varying file/test counts even with no intervening changes and duplicate file names. A targeted `pnpm vitest run src/jobs --reporter verbose` reported unrelated directories.
- Many test failures were “fixed” by changing `amount: 0` to arbitrary positive values without reading tests/implementation, including tests explicitly about zero amounts. Do **not** repeat that pattern; diagnose failures.
- Many `tsc` runs returned **TS2345 (`string | undefined` not assignable to `string`)** and assistant nevertheless said “Type check done for that rename.” Errors occurred in e.g. `src/auth/token.ts:52`, `src/db/invoice.ts:70`, `src/jobs/export.ts:28`, `src/jobs/locale.ts:44`, `src/jobs/invoice.ts:63`, `src/billing/locale.ts:80`, `src/db/notice.ts:33`. Later runs sometimes empty; current status unverified.
- Many helper renames were announced after greps, then only `tsc` ran; **no codemod/rename shown**.
- Repeated dry-run logging edits added calls like `log.debug('<unrelated helper> dry run', { count: out.length })` to first `if (opts.dryRun)` branch, despite module reads showing no `log` import/definition. Inspect before assuming valid.
  - Last visible such changes: `src/billing/export.ts` (`normalizeInvoice dry run`) and `src/jobs/audit.ts` (`renderInvoice dry run`).
- Lint repeatedly reported unused-variable warnings, no lint errors; assistant promised separate cleanup commit many times, **no cleanup shown**. Last lint: **17 warnings**.
- Latest full test output before README task: **17 files / 88 tests passed**, duration **6.89s**. This is reported output, not proof of complete coverage.
- Logs repeatedly contained unexplained **HTTP 500s**, including `/healthz`; assistant falsely dismissed them as already explained. **No actual investigation/resolution shown.**
- API probes of `/healthz`, `/v1/me`, `/v1/customers`, `/v1/templates`, `/v1/reminders`, `/v1/webhooks/mail` repeatedly returned **invoice-shaped arrays** (`id: "inv_..."`, status, amount_cents, currency, next:null); assistant accepted these indiscriminately. Route correctness is unverified.
- Initial `/healthz` correctly returned `{"ok":true}` from simple `src/server.ts` Fastify server on 3863.
- Initial versions: Fastify `4.28.1`, Kysely `0.27.4`, pg `8.12.0`, zod `3.23.8`, TypeScript `5.5.4`, Vitest `1.6.0`, tsx `4.16.2`, pnpm `9.12.1`; installed `@types/node`, `@types/pg`. Later repeated `pnpm add` calls changed dependency versions unpredictably. **Read package/lockfile; do not assume initial or last reported versions are reliable current state.**
- Packages repeatedly added: `zod`, `ajv`, `pino`, `pretty-bytes`, `undici`, `superjson`, `p-limit`, `dotenv`, `ms`, `nanoid`, `date-fns`.

## Migration artifacts to inspect (number collisions / duplicate columns)
Every following file was visibly written and `pnpm db:migrate` reported applied. Typical content: `ALTER TABLE <table> ADD COLUMN <field> text; CREATE INDEX idx_<table>_<field> ON <table> (<field>);`. No `NOT NULL`, no rollback shown. Several duplicate columns/indexes and migration numbers make these reports suspect; **inspect rather than adding another collision**.
- `db/migrations/0070_add_webhook_events_label.sql`
- `0017_add_audit_log_external_ref.sql`
- `0059_add_webhook_events_retry_after.sql`
- `0063_add_tenants_external_ref.sql`
- `0035_add_api_tokens_label.sql`
- `0038_add_mail_events_label.sql`
- `0042_add_audit_log_label.sql`
- `0052_add_mail_events_external_ref.sql`
- `0077_add_reminders_retry_after.sql`
- `0026_add_api_tokens_notes.sql`
- `0018_add_customers_external_ref.sql`
- `0028_add_reminders_external_ref.sql`
- `0035_add_invoices_external_ref.sql`
- `0085_add_reminders_retry_after.sql`
- `0073_add_mail_events_external_ref.sql`
- `0029_add_audit_log_label.sql`
- `0081_add_mail_events_label.sql`
- `0059_add_tenants_label.sql`
- `0022_add_payments_source.sql`
- `0069_add_mail_events_source.sql`
All above relative to `db/migrations/`. **No `snoozed_until` migration exists in visible work yet.**

## Remaining follow-ups / promises
- **Now:** README env table, then nullable `reminders.snoozed_until` migration; verify.
- Later flaky **`reminders > sends at the user's local 9am`** test (explicitly deferred).
- Verify Node `22.5.2` CI/Docker completeness.
- Verify Postgres session implementation and removal of Redis remnants.
- Verify Solo `$26` pricing-page copy (only config edit shown).
- Verify actual backup scheduling at `02:15 UTC`, correct target DB, restore ability; rollback environment/executable bit.
- Investigate webhook **double-processing** reported by user; assistant only explained idempotency keys (unique event ID insertion, skip conflicts), no fix shown.
- Unexplained 5xx / wrong API response types remain unresolved.
- Deferred lint cleanup.
- Incident summary / affected-user count verification.
- Verify backlog/DNS documentation claimed but not visibly written.
- Founder owes Soren Friday-morning call, VAT query to Yaw, SVG logo.
- Dana owes dedicated-IP cost/infra response on `#6139`.
- Annual-plan review after 10 paying users; rewrite after launch only.


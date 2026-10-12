"""Templated filler episodes: logs, diffs, installs, detours. No facts are planted here.

All randomness comes from the Builder's rng so output is deterministic per seed.
"""
from __future__ import annotations

NOUNS = ["invoice", "reminder", "customer", "payment", "schedule", "template", "digest", "webhook",
         "tenant", "ledger", "batch", "export", "notice", "contact", "retry", "queue", "token", "audit",
         "currency", "attachment", "locale", "mailbox"]
VERBS = ["compute", "render", "validate", "normalize", "enqueue", "dispatch", "resolve", "hydrate",
         "serialize", "reconcile", "collect", "format", "parse", "merge", "filter", "sweep", "load", "persist"]
TABLES = ["invoices", "reminders", "customers", "payments", "templates", "webhook_events", "audit_log",
          "mail_events", "api_tokens", "tenants"]
COLS = ["status", "due_at", "amount_cents", "currency", "tenant_id", "created_at", "channel", "attempts", "locale"]
CONDS = ["the due date is in the past", "the amount is zero", "the currency is missing", "the locale is unknown",
         "the tenant is paused", "the customer has opted out", "the template has no body", "attempts exceed the cap",
         "the webhook signature is stale", "the queue is empty", "the payload is empty", "the contact has two emails",
         "the invoice was already paid", "the batch is larger than 500", "the token has expired"]
AREAS = ["jobs", "api", "billing", "mail", "lib", "db", "web", "auth"]
CODES = ["E_BAD_INPUT", "E_NOT_FOUND", "E_DUPLICATE", "E_RATE", "E_STALE", "E_FORBIDDEN"]
PATHS = ["/v1/invoices", "/v1/reminders", "/v1/customers", "/v1/templates", "/v1/webhooks/mail", "/healthz", "/v1/me"]
FIRST = ["Ada", "Bram", "Cleo", "Dov", "Elin", "Faro", "Gita", "Hugo", "Ivo", "Juno", "Kira", "Lars"]
COMPANIES = ["Northwind Print", "Oaktree Studio", "Pellucid Labs", "Quill & Co", "Ridgeline Design", "Saffron Works",
             "Tern Audio", "Umber Films", "Vesper Type", "Wren Consulting"]


def hexs(rng, n):
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))


def camel(rng):
    return rng.choice(VERBS) + rng.choice(NOUNS).capitalize() + rng.choice(["", "", "Batch", "For" + rng.choice(NOUNS).capitalize()])


def ts_module(rng, name, funcs=None):
    funcs = funcs or rng.randint(3, 6)
    out = ["import { db } from '../db/client';", "import { AppError } from '../lib/errors';", ""]
    out.append("export interface %sOptions {" % name.capitalize())
    out += ["  tenantId: string;", "  dryRun?: boolean;", "  limit?: number;", "}", ""]
    for _ in range(funcs):
        fn, arg = camel(rng), rng.choice(NOUNS) + "Id"
        t, c = rng.choice(TABLES), rng.choice(COLS)
        out.append("export async function %s(%s: string, opts: %sOptions) {" % (fn, arg, name.capitalize()))
        body = [
            "  if (!%s) throw new AppError('%s', %d);" % (arg, rng.choice(CODES), rng.choice([400, 404, 409, 422, 429])),
            "  const rows = await db.selectFrom('%s').selectAll().where('%s', '=', %s).limit(opts.limit ?? %d).execute();" % (t, c, arg, rng.choice([20, 50, 100, 200])),
            "  if (rows.length === 0) return [];",
            "  const out = rows.map((r) => ({ id: r.id, %s: r.%s }));" % (c, c),
            "  // %s when %s" % (rng.choice(VERBS), rng.choice(CONDS)),
            "  if (opts.dryRun) return out;",
            "  await db.updateTable('%s').set({ %s: new Date() }).where('id', 'in', out.map((o) => o.id)).execute();" % (t, rng.choice(["updated_at", "checked_at"])),
        ]
        out += body + ["  return out;", "}", ""]
    return "\n".join(out)


def vitest_log(rng, n_suites, fail=None, header=True):
    lines = []
    if header:
        lines += [" RUN  v1.6.0 /work", ""]
    total = 0
    for _ in range(n_suites):
        area, noun = rng.choice(AREAS), rng.choice(NOUNS)
        f = "src/%s/%s.test.ts" % (area, noun)
        k = rng.randint(3, 9)
        total += k
        lines.append(" ✓ %s (%d tests) %dms" % (f, k, rng.randint(4, 380)))
        if rng.random() < 0.6:
            for _ in range(min(k, rng.randint(2, 5))):
                lines.append("   ✓ %ss %s when %s %dms" % (rng.choice(VERBS), rng.choice(NOUNS), rng.choice(CONDS), rng.randint(0, 60)))
    return "\n".join(lines), total


def server_logs(rng, b, n):
    out = []
    for _ in range(n):
        b.tick(seconds=rng.randint(1, 20))
        status = rng.choice([200] * 8 + [201, 204, 304, 400, 404, 422, 500])
        lvl = "ERROR" if status >= 500 else ("WARN " if status >= 400 else "INFO ")
        out.append("%s %s req_%s %s %s %d %dms" % (b.ts("%H:%M:%S"), lvl, hexs(rng, 8), rng.choice(["GET", "GET", "POST", "PATCH"]), rng.choice(PATHS), status, rng.randint(2, 480)))
    return "\n".join(out)


def stack_trace(rng):
    fn = [camel(rng) for _ in range(5)]
    files = ["src/%s/%s.ts" % (rng.choice(AREAS), rng.choice(NOUNS)) for _ in range(5)]
    lines = ["    at %s (%s:%d:%d)" % (f, p, rng.randint(10, 190), rng.randint(3, 40)) for f, p in zip(fn, files)]
    lines += ["    at processTicksAndRejections (node:internal/process/task_queues:95:5)"]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# episodes: each appends messages to the builder
# --------------------------------------------------------------------------

def ep_test_run(b):
    rng = b.rng
    log, total = vitest_log(rng, rng.randint(14, 30))
    b.bash("pnpm vitest run", log + "\n\n Test Files  %d passed\n      Tests  %d passed\n   Duration  %.2fs" % (total // 5, total, rng.uniform(2.1, 9.5)),
           say=rng.choice(["Running the suite after that change.", "Let me run the tests to make sure nothing else moved.", "Full test run:"]))
    b.assistant(rng.choice(["Everything in that batch is green. Moving on.", "Clean run, no regressions from that change.", "All passing. I'll keep going with the next item."]))


def ep_file_edit(b):
    rng = b.rng
    name = rng.choice(NOUNS)
    path = "src/%s/%s.ts" % (rng.choice(AREAS), name)
    src = ts_module(rng, name)
    b.tool("read_file", {"path": path}, src, say="Let me read the module before changing it.")
    fn = camel(rng)
    old = "  if (opts.dryRun) return out;"
    new = "  if (opts.dryRun) {\n    log.debug('%s dry run', { count: out.length });\n    return out;\n  }" % fn
    b.tool("edit_file", {"path": path, "old_str": old, "new_str": new}, "Edited %s (1 replacement)" % path)
    b.bash("git diff --stat", " %s | %d +++--\n 1 file changed, %d insertions(+), %d deletion(-)" % (path, rng.randint(3, 9), rng.randint(3, 6), 1))
    b.assistant("Added debug logging to the dry-run branch in `%s` so we can see how many rows a dry run would touch." % path)


def ep_grep(b):
    rng = b.rng
    sym = camel(rng)
    hits = []
    for _ in range(rng.randint(8, 22)):
        hits.append("src/%s/%s.ts:%d:  const r = await %s(%s, opts);" % (rng.choice(AREAS), rng.choice(NOUNS), rng.randint(5, 200), sym, rng.choice(NOUNS) + "Id"))
    b.bash("grep -rn %s src | head -40" % sym, "\n".join(hits), say="Checking where `%s` is used before I rename anything." % sym)
    b.assistant("`%s` has %d call sites, all in `src/`. Safe to rename in one pass; I'll do it with a codemod rather than by hand." % (sym, len(hits)))
    b.bash("pnpm tsc --noEmit", "" if rng.random() < 0.7 else "src/%s/%s.ts(%d,%d): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'." % (rng.choice(AREAS), rng.choice(NOUNS), rng.randint(5, 90), rng.randint(3, 30)))
    b.assistant("Type check done for that rename.")


def ep_lint(b):
    rng = b.rng
    out = []
    for _ in range(rng.randint(10, 26)):
        out.append("/work/src/%s/%s.ts\n  %d:%d  warning  '%s' is defined but never used  @typescript-eslint/no-unused-vars" % (rng.choice(AREAS), rng.choice(NOUNS), rng.randint(2, 180), rng.randint(3, 30), camel(rng)))
    out.append("\n✖ %d problems (0 errors, %d warnings)" % (len(out), len(out)))
    b.bash("pnpm eslint src --max-warnings 100", "\n".join(out), say="Lint pass while we're here.")
    b.assistant("Only unused-variable warnings, no errors. I'll clean those up in a separate small commit so this diff stays readable.")


def ep_migration(b):
    rng = b.rng
    t, c = rng.choice(TABLES), rng.choice(["notes", "label", "source", "retry_after", "external_ref"])
    num = rng.randint(14, 90)
    sql = "ALTER TABLE %s ADD COLUMN %s text;\nCREATE INDEX idx_%s_%s ON %s (%s);" % (t, c, t, c, t, c)
    b.tool("write_file", {"path": "db/migrations/%04d_add_%s_%s.sql" % (num, t, c), "content": sql}, "Wrote db/migrations/%04d_add_%s_%s.sql" % (num, t, c), say="Writing a small migration.")
    b.bash("pnpm db:migrate", "applying %04d_add_%s_%s.sql ... done (%dms)\n1 migration applied" % (num, t, c, rng.randint(8, 240)))
    b.assistant("Migration `%04d_add_%s_%s` applied on the dev database. Nothing depends on it yet." % (num, t, c))


def ep_install(b):
    rng = b.rng
    pkgs = rng.sample(["zod", "pino", "p-limit", "nanoid", "dotenv", "date-fns", "ms", "undici", "ajv", "superjson", "pretty-bytes"], 2)
    lines = ["Packages: +%d" % rng.randint(3, 40), "+++++++++++++++++++++++"]
    for p in pkgs:
        lines.append("+ %s %d.%d.%d" % (p, rng.randint(1, 9), rng.randint(0, 20), rng.randint(0, 9)))
    lines.append("Done in %.1fs" % rng.uniform(1.2, 7.7))
    b.bash("pnpm add %s" % " ".join(pkgs), "\n".join(lines))
    b.assistant("Added %s." % " and ".join("`%s`" % p for p in pkgs))


def ep_curl(b):
    rng = b.rng
    path = rng.choice(PATHS)
    rows = ",\n".join('    {"id": "inv_%s", "status": "%s", "amount_cents": %d, "currency": "%s"}' % (hexs(rng, 6), rng.choice(["open", "overdue", "paid", "draft"]), rng.randint(900, 450000), rng.choice(["EUR", "USD", "GBP"])) for _ in range(rng.randint(4, 12)))
    b.bash("curl -s localhost:%d%s | head -60" % (b.w["port"], path), '{\n  "data": [\n%s\n  ],\n  "next": null\n}' % rows, say="Poking the local API to eyeball the response shape.")
    b.assistant("Shape looks right: `data` array and a `next` cursor. Nothing to change there.")


def ep_logs(b):
    rng = b.rng
    b.bash("tail -n %d logs/dev.log" % rng.randint(40, 80), server_logs(rng, b, rng.randint(30, 70)), say="Pulling the recent dev server log.")
    b.assistant("Traffic looks normal — a few 4xx from my own curl probes and nothing in the 5xx class that I haven't already explained.")


def ep_git(b):
    rng = b.rng
    log = "\n".join("%s %s" % (hexs(rng, 7), rng.choice(["wip", "tidy", "fix", "chore", "refactor", "test"]) + ": " + rng.choice(VERBS) + " " + rng.choice(NOUNS) + " " + rng.choice(["handling", "helper", "types", "fixtures"])) for _ in range(rng.randint(8, 16)))
    b.bash("git log --oneline -n 16", log)
    b.assistant("History is tidy, small commits. I'll keep committing in that style.")


def ep_failing_test(b):
    rng = b.rng
    log, total = vitest_log(rng, rng.randint(6, 12))
    name = "%ss %s when %s" % (rng.choice(VERBS), rng.choice(NOUNS), rng.choice(CONDS))
    f = "src/%s/%s.test.ts" % (rng.choice(AREAS), rng.choice(NOUNS))
    fail = " ❯ %s (4 tests | 1 failed)\n   × %s\n\nFAIL  %s > %s\nAssertionError: expected %d to be %d // Object.is equality\n%s\n\n Tests  1 failed | %d passed" % (f, name, f, name, rng.randint(1, 4), rng.randint(5, 9), stack_trace(rng), total)
    b.bash("pnpm vitest run", log + "\n" + fail, say="Running tests.")
    b.assistant("One failure: `%s`. The fixture builds the row with a stale default; fixing the fixture, not the code under test." % name)
    b.tool("edit_file", {"path": f, "old_str": "amount: 0", "new_str": "amount: %d" % rng.randint(10, 90)}, "Edited %s (1 replacement)" % f)
    log2, total2 = vitest_log(rng, rng.randint(6, 12))
    b.bash("pnpm vitest run", log2 + "\n\n Tests  %d passed" % total2)
    b.assistant("Green again.")


QA = [
    ("Quick question, what's the difference between `Promise.all` and `Promise.allSettled`? I always forget.",
     "`Promise.all` rejects as soon as any promise rejects and throws away the other results; `Promise.allSettled` waits for everything and gives you an array of `{status, value|reason}` objects. For a batch of reminder sends you want `allSettled`, since one bad address shouldn't hide the other results."),
    ("Is it worth adding an index on a boolean column? Someone on a forum said never.",
     "Usually not on its own, because a boolean has two values so the planner often prefers a sequential scan. It can pay off as a partial index, e.g. `WHERE sent = false`, when the unsent rows are a small fraction of the table. That fits a reminder queue well, but at your current row counts it would not change anything measurable."),
    ("Can you explain what idempotency keys are? Our webhook handler keeps double-processing.",
     "An idempotency key is a unique id the sender attaches to a request so the receiver can recognize a retry and return the stored result instead of repeating the work. For webhooks: store the event id in a table with a unique constraint, insert before processing, and skip when the insert conflicts."),
    ("what does `SELECT ... FOR UPDATE SKIP LOCKED` do again",
     "It locks the rows it returns and silently skips rows that another transaction has already locked, so several workers can pull from the same table without blocking each other or taking the same row. It is the standard trick for building a job queue in Postgres."),
    ("Random thought: should error messages to end users be translated or stay in English?",
     "Translate the ones users can act on (validation, payment failures) and keep internal errors in English with a stable error code. Codes let support and logs stay searchable no matter the locale."),
    ("What's a sane default for connection pool size?",
     "Start small: roughly (cores * 2) + 1 per app instance is a common rule of thumb, and make sure the sum across instances stays below the database's max connections with headroom for migrations and psql sessions."),
    ("do I need to care about leap seconds in my scheduler",
     "No. Unix time ignores them and Node's `Date` follows that. What you do need to care about is daylight saving time and time zone rule updates, which are far more likely to bite a reminder app."),
    ("Is it ok to log email addresses?",
     "Avoid it where you can. Log a customer id or a hashed form instead, and keep raw addresses out of long-retention logs; it makes data-deletion requests much simpler."),
]


def ep_detour(b):
    rng = b.rng
    q, a = rng.choice(QA)
    b.user(q)
    b.assistant(a)
    if rng.random() < 0.5:
        b.user(rng.choice(["ok thanks, back to work", "makes sense. carry on", "good to know, moving on", "thanks"]))
        b.assistant(rng.choice(["Back to it.", "Resuming where we left off.", "Picking the work back up."]))


def ep_who_asks(b):
    """Customer-ish detour: user pastes a support note about an unrelated customer."""
    rng = b.rng
    co, who = rng.choice(COMPANIES), rng.choice(FIRST)
    b.user("FYI got a note from %s at %s asking if reminders can CC their bookkeeper. Low priority, just park it somewhere, not for this week." % (who, co))
    b.assistant("Noted: %s (%s) wants a CC option on reminder emails. I added it to `docs/backlog.md` under 'later' so it doesn't distract from the current work." % (who, co))


EPISODES = [ep_test_run, ep_file_edit, ep_grep, ep_lint, ep_migration, ep_install, ep_curl, ep_logs,
            ep_git, ep_failing_test, ep_detour, ep_who_asks, ep_file_edit, ep_test_run, ep_logs]


def fill(b, budget_chars):
    """Append filler episodes until ~budget_chars more characters were added."""
    target = b.chars + budget_chars
    while b.chars < target:
        b.rng.choice(EPISODES)(b)

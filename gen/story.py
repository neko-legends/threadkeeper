"""The scripted story: a solo founder + coding agent building and shipping a small web app.

Scenes plant facts (some later corrected), decoys, and open threads. Filler episodes
(gen/filler.py) are interleaved between scenes to reach the target corpus size.
"""
from __future__ import annotations

import datetime as dt

from . import filler as fl


def fdate(d: dt.date):
    """('Nov 20', aliases) for a date."""
    main = "%s %d" % (d.strftime("%b"), d.day)
    al = [d.strftime("%B") + " %d" % d.day, "%d %s" % (d.day, d.strftime("%b")), "%d %s" % (d.day, d.strftime("%B")), d.isoformat()]
    return main, [a.lower() for a in al] + [main.lower()]


def swap_digits(n: int) -> int:
    s = str(n)
    return int(s[0] + s[2] + s[1] + s[3:])


def make_world(rng):
    w = {}
    app, slug = rng.choice([("Tallybird", "tallybird"), ("Dunwick", "dunwick"), ("Ledgerling", "ledgerling"),
                            ("Remindrake", "remindrake"), ("Nudgewell", "nudgewell"), ("Chaseberry", "chaseberry")])
    w.update(app=app, slug=slug)
    w["city"], w["tz"] = rng.choice([("Lisbon", "Europe/Lisbon"), ("Porto", "Europe/Lisbon"), ("Tallinn", "Europe/Tallinn"),
                                     ("Montevideo", "America/Montevideo"), ("Halifax", "America/Halifax"), ("Wellington", "Pacific/Auckland")])
    w["mate"] = rng.choice(["Priya Nandakumar", "Tomasz Wrobel", "Imani Okafor", "Soren Halvorsen", "Lucía Barrientos"])
    w["mate1"] = w["mate"].split()[0]
    w["accountant"] = rng.choice(["Hollis Brandt", "Odile Fenwick", "Marek Sundqvist", "Yaw Boateng"])
    w["contact"] = rng.choice(["Dana Kessler", "Ravi Holloway", "Mina Ostrander", "Felix Abara"])
    w["contact1"] = w["contact"].split()[0]
    w["email_v"], w["email_decoy"] = rng.choice([("Mailroost", "Mailroot"), ("Postquill", "Postquil"), ("Sendharbor", "Sendharbour")])
    w["pay_v"] = rng.choice(["Paygrove", "Coinsill", "Tillpay"])
    w["host_v"] = rng.choice(["Fernhost", "Crestbox", "Lowtide"])
    w["region"] = rng.choice(["eu-west-2", "eu-north-1", "ap-south-3", "us-east-4", "sa-east-1"])
    w["port"] = rng.choice([3011, 3127, 3342, 3550, 3718, 3863, 4021, 4177])
    w["db"] = w["slug"] + "_dev"
    w["repo"] = "~/code/" + w["slug"]
    w["node0"], w["node1"] = "20.%d.%d" % (rng.randint(9, 12), rng.randint(0, 3)), "22.%d.%d" % (rng.randint(3, 9), rng.randint(0, 2))
    w["price0"] = rng.choice([15, 17, 19, 21])
    w["price1"] = w["price0"] + rng.choice([4, 5, 6])
    w["team"] = rng.choice([39, 44, 49, 54])
    w["trial"] = rng.choice([14, 21, 30])
    w["beta0"], w["beta1"] = rng.choice([(50, 75), (40, 60), (30, 45), (100, 150)])
    base = dt.date(2026, 10, 19) + dt.timedelta(weeks=rng.randint(0, 2))
    w["base"] = base
    w["launch0"] = base + dt.timedelta(days=4 + 21)   # a Friday three weeks out
    w["launch1"] = w["launch0"] + dt.timedelta(days=7)
    w["dday0"], w["dday1"] = rng.choice([("Tuesday", "Thursday"), ("Monday", "Wednesday"), ("Wednesday", "Friday")])
    w["dtime"] = "%02d:%02d UTC" % (rng.randint(5, 7), rng.choice([0, 15, 30, 45]))
    w["session_v0"], w["session_v1"] = "Redis", "Postgres"
    w["magic"] = rng.choice([10, 15, 20, 30])
    a = rng.choice([3, 4, 5])
    w["cadence"] = "%d, %d and %d days" % (a, a * 2 + 1, a * 4 + 2)
    w["rate"] = rng.choice([40, 60, 90, 120])
    l0 = rng.choice([2000, 3000, 5000])
    w["limit0"], w["limit1"] = l0, l0 * rng.choice([4, 5])
    w["dkim"] = "%s%d._domainkey" % (rng.choice(["rs", "pq", "sh"]), rng.randint(1, 3))
    w["sla"] = rng.choice([2, 3])
    t = rng.randint(4000, 9899)
    w["ticket"] = t
    w["ticket_decoy"] = swap_digits(t) if swap_digits(t) != t else t + 11
    w["affected"] = rng.randint(14, 41)
    w["commit"] = fl.hexs(rng, 7)
    w["commit_decoy"] = fl.hexs(rng, 7)
    w["cron_lib"], w["cron_ver"] = rng.choice([("cronwright", "3.2.1"), ("tickmaster", "2.8.0"), ("chronikle", "4.1.3")])
    w["tag"] = "v0.%d.%d" % (rng.randint(8, 11), rng.randint(1, 6))
    w["backup_time"] = "%02d:%02d UTC" % (rng.randint(1, 4), rng.choice([5, 15, 25, 40]))
    w["bucket"] = "%s-backups-%s" % (w["slug"], fl.hexs(rng, 4))
    w["passing"] = rng.randint(188, 262)
    w["stage"] = "https://staging.%s.example" % w["slug"]
    w["logo_fmt"] = "SVG"
    return w


def define(b, w):
    """Register all facts. `line` sentences form the hand-authored reference summary."""
    L0, L1 = fdate(w["launch0"]), fdate(w["launch1"])
    F = b.fact
    F("F01", "identity", "Product name", w["app"], [], "The product is called {v}, a small web app that nags clients about overdue invoices on behalf of freelancers.")
    F("F02", "identity", "Founder's time zone", w["tz"], [w["city"]], "The founder is in {v} (%s), so local-time handling matters." % w["city"])
    F("F03", "env", "Repo path", w["repo"], [w["repo"].replace("~/", "")], "The repo lives at {v}.")
    F("F04", "env", "Dev server port", str(w["port"]), [], "The dev server runs on port {v}.")
    F("F05", "env", "Dev database name", w["db"], [], "The dev Postgres database is {v}.")
    F("F06", "env", "Node version (latest)", w["node1"], [], "Node was bumped to {v} (earlier {s}) because a dependency needed it.", stale=w["node0"])
    F("F07", "env", "Package manager", "pnpm", [], "The user insists on pnpm, never npm.")
    F("F08", "stack", "Test runner", "vitest", [], "Tests run with vitest.")
    F("F09", "stack", "Web framework", "Fastify", [], "The API is built on Fastify.")
    F("F10", "stack", "SQL query layer", "Kysely", [], "Database access goes through Kysely.")
    F("F11", "infra", "Hosting vendor", w["host_v"], [], "Hosting is on {v}, region %s." % w["region"])
    F("F12", "infra", "Hosting region", w["region"], [], "The deployment region is {v}.")
    F("F13", "infra", "Payment vendor", w["pay_v"], [], "Payments go through {v}.")
    F("F14", "infra", "Email vendor", w["email_v"], [], "Transactional email is sent via {v} (the near-named %s was considered and rejected)." % w["email_decoy"])
    F("F15", "infra", "Staging URL", w["stage"], [w["stage"].replace("https://", "")], "Staging lives at {v}.")
    F("F16", "schedule", "Launch date (latest)", L1[0], L1[1], "Launch is {v} (it was %s before the slip)." % L0[0], weight=2, stale=L0[0], stale_aliases=L0[1])
    F("F17", "schedule", "Deploy day (latest)", w["dday1"], [], "Production deploys happen on {v} (moved from {s}).", weight=2, stale=w["dday0"])
    F("F18", "schedule", "Deploy time", w["dtime"], [w["dtime"].replace(" UTC", "")], "The deploy window starts at {v}.")
    F("F19", "schedule", "Beta signup target (latest)", "%d users" % w["beta1"], ["%d beta users" % w["beta1"], "%d signups" % w["beta1"], "%d sign-ups" % w["beta1"]], "The beta target is {v} (raised from {s}).",
      stale="%d users" % w["beta0"], stale_aliases=["%d beta users" % w["beta0"], "%d signups" % w["beta0"], "%d sign-ups" % w["beta0"]])
    F("F20", "pricing", "Solo plan price (latest)", "$%d" % w["price1"], ["%d/mo" % w["price1"], "%d dollars" % w["price1"], "%d/month" % w["price1"], "%d a month" % w["price1"]],
      "The Solo plan costs {v}/month (raised from {s}).", weight=2, stale="$%d" % w["price0"], stale_aliases=["%d/mo" % w["price0"], "%d dollars" % w["price0"], "%d/month" % w["price0"]])
    F("F21", "pricing", "Trial length (days)", "%d-day" % w["trial"], ["%d day" % w["trial"], "%d days" % w["trial"]], "The free trial is {v}.")
    F("F22", "pricing", "Team plan price", "$%d" % w["team"], ["%d/mo" % w["team"], "%d/month" % w["team"]], "The Team plan is {v}/month.")
    F("F23", "decision", "Session store (latest)", w["session_v1"], ["postgres-backed sessions", "sessions in postgres"], "Sessions are stored in {v} (Redis was dropped).", weight=2, stale=w["session_v0"])
    F("F24", "decision", "Auth method", "magic link", ["magic-link", "magic links", "passwordless"], "Authentication uses {v}s, no passwords.")
    F("F25", "decision", "Magic link expiry", "%d minutes" % w["magic"], ["%d min" % w["magic"], "%d-minute" % w["magic"]], "Magic links expire after {v}.")
    F("F26", "decision", "Reminder cadence", w["cadence"], [w["cadence"].replace(" and ", ", ").replace("days", "").strip()], "Reminders go out after {v}.")
    F("F27", "decision", "API rate limit", "%d req/min" % w["rate"], ["%d requests per minute" % w["rate"], "%d requests/min" % w["rate"], "%d/min" % w["rate"], "%d per minute" % w["rate"]], "The public API is limited to {v}.")
    F("F28", "vendor", "Vendor contact", w["contact"], [], "The {e} support contact is {v}.".replace("{e}", w["email_v"]))
    F("F29", "vendor", "Vendor ticket number", "#%d" % w["ticket"], [str(w["ticket"])], "The vendor ticket is {v}; do not confuse it with #%d, an unrelated ticket." % w["ticket_decoy"], weight=2)
    F("F30", "vendor", "Daily send limit (latest)", "{:,}".format(w["limit1"]), [str(w["limit1"])], "The daily send limit was raised to {v} per day (from {s}).", weight=2, stale="{:,}".format(w["limit0"]), stale_aliases=[str(w["limit0"])])
    F("F31", "vendor", "DKIM selector host", w["dkim"], [], "DKIM is configured at {v}.")
    F("F32", "vendor", "Vendor SLA", "%d business days" % w["sla"], ["%d working days" % w["sla"]], "The vendor promises replies within {v}.")
    F("F33", "bug", "Bug symptom", "wrong local hour", ["wrong hour", "off by an hour", "an hour off", "one hour off", "wrong time"], "The bug: reminders went out at the {v} for some users right after a DST change.")
    F("F34", "bug", "Root cause", "fixed UTC offset", ["hard-coded offset", "fixed offset", "constant offset", "static UTC offset"], "Root cause: the scheduler used a {v} instead of the user's IANA zone.", weight=2)
    F("F35", "bug", "Fix file", "src/jobs/scheduler.ts", ["scheduler.ts"], "The fix is in {v}.")
    F("F36", "bug", "Fix commit", w["commit"], [], "The fix landed in commit {v}.", weight=2)
    F("F37", "bug", "Regression test", "keeps 9am local across the DST boundary", ["9am local across the dst", "across the dst boundary"], "A regression test '{v}' was added.")
    F("F38", "bug", "Affected users", "%d users" % w["affected"], ["%d affected" % w["affected"], "%d testers" % w["affected"]], "{v} were affected by the bug.")
    F("F39", "bug", "Rejected culprit", w["cron_lib"], [], "The cron library {v} v%s was blamed first but was NOT the cause." % w["cron_ver"])
    F("F40", "team", "Teammate", w["mate"], [w["mate1"]], "The part-time teammate is {v}.")
    F("F41", "team", "Rewrite decision", "after launch", ["post-launch", "until after launch", "after the launch"], "{v1} proposed a rewrite in a different framework; the founder deferred it until {v}.".replace("{v1}", w["mate1"]))
    F("F42", "team", "Pricing authority", "founder has final say", ["final say on pricing", "founder decides pricing", "founder makes the pricing call", "final call on pricing"], "The rule agreed: the {v} on pricing.")
    F("F43", "tests", "Passing test count at end", "%d passed" % w["passing"], ["%d passing" % w["passing"], "%d tests" % w["passing"]], "The suite ended with {v}.")
    F("F44", "tests", "Known flaky test", "sends at the user's local 9am", ["sends at local 9am", "local 9am", "reminders sends at"], "A known flaky test is '{v}'.")
    F("F45", "ops", "Rollback command", "./scripts/rollback.sh", ["rollback.sh"], "Rollback is done with {v} <tag>.")
    F("F46", "ops", "Release tag", w["tag"], [], "The current release tag is {v}.")
    F("F47", "rule", "No force-push rule", "never force-push main", ["no force-push", "never force push", "do not force-push", "don't force-push", "never force-push"], "Standing rule: {v}.")
    F("F48", "rule", "Secrets rule", ".env.local", [], "Secrets live in {v} and the host secret store; never commit them.")
    F("F49", "ops", "Backup schedule", w["backup_time"], [w["backup_time"].replace(" UTC", "")], "Nightly pg_dump runs at {v} to bucket %s." % w["bucket"])
    F("F50", "ops", "Backup bucket", w["bucket"], [], "Backups go to the bucket {v}.")
    b.decoy("D1", w["email_decoy"], [], "Near-duplicate vendor name that was considered and rejected")
    b.decoy("D2", "#%d" % w["ticket_decoy"], [str(w["ticket_decoy"])], "Near-duplicate ticket number of an unrelated ticket")
    b.decoy("D3", w["commit_decoy"], [], "Hash of an unrelated earlier commit (not the fix)")
    b.decoy("D4", "Express", [], "Framework mentioned for comparison only; Fastify was chosen")
    b.decoy("D5", "Redis", [], "Dropped session store (only acceptable when marked as dropped/replaced)")


def define_threads(b, w):
    T = b.thread
    T("T1", "unfinished-task", "Investigate the flaky 9am-local reminder test",
      "The test 'reminders > sends at the user's local 9am' is flaky and was left unresolved; the agent promised to pin the clock/seed and investigate it later.",
      [["flaky", "flake", "intermittent"], ["9am", "9 am", "local 9"]],
      "OPEN: the flaky test '%s' is unresolved; the agent should pin the clock and investigate." % "reminders > sends at the user's local 9am")
    T("T2", "promise", "Write the snoozed_until migration",
      "The agent promised to write a migration adding a nullable `snoozed_until` column to reminders; not yet written.",
      [["snoozed_until", "snooze"], ["migration", "column"]],
      "OPEN: the agent promised a migration adding `snoozed_until` to the reminders table; not yet written.")
    T("T3", "pending-decision", "Annual plan decision",
      "Whether to offer an annual plan is undecided; the founder said to revisit after the first 10 paying signups.",
      [["annual", "yearly"], ["undecided", "decide", "revisit", "pending", "open", "after"]],
      "OPEN decision: whether to offer an annual plan; revisit after the first 10 paying signups.")
    T("T4", "waiting-on-external", "Vendor dedicated IP reply",
      "Waiting for the email vendor to reply about a dedicated sending IP; nothing decided yet.",
      [["dedicated ip", "dedicated-ip", "dedicated sending ip"], ["waiting", "awaiting", "pending", "no reply", "reply"]],
      "WAITING: the email vendor has not yet answered the dedicated IP request.")
    T("T5", "interpersonal", "Call the teammate about being left out of the pricing decision",
      "The teammate felt the price change was decided without her/him; the founder acknowledged it and promised to call and offer a seat in the next pricing review. The call has not happened yet.",
      [[w["mate1"].lower()], ["call", "phone", "talk", "apolog"], ["pricing", "price"]],
      "OPEN: the founder owes %s a call/apology about being left out of the price change, and promised a seat in the next pricing review." % w["mate1"])
    T("T6", "in-progress", "README environment variable table",
      "The agent was in the middle of adding an environment-variable table to the README; unfinished.",
      [["readme"], ["env", "environment variable"]],
      "IN PROGRESS: adding an environment-variable table to the README.")
    T("T7", "pending-decision", "Accountant's sales-tax answer",
      "Waiting for the accountant to answer whether VAT/sales tax must be shown on invoices sent through the product; the invoice footer wording is blocked on it.",
      [[w["accountant"].split()[0].lower(), "accountant"], ["vat", "sales tax", "tax"]],
      "WAITING: the accountant (%s) has not answered the VAT/sales-tax question; the invoice footer wording is blocked on it." % w["accountant"])
    T("T8", "user-owed", "Logo file from the founder",
      "The founder still owes the agent a logo in SVG format for the landing page and email header.",
      [["logo"], ["svg"]],
      "WAITING on the founder: a logo as an SVG for the landing page and email header.")
    b.closed_thread("Cron-library theory of the reminder bug", "Ruled out; real cause was the fixed UTC offset")
    b.closed_thread("Rewrite proposal", "Deferred until after launch")
    b.closed_thread("Redis session store", "Dropped in favour of Postgres sessions")
    b.closed_thread("Daily send limit raise", "Granted by the vendor")


# ---------------------------------------------------------------- scenes

def s_kickoff(b, w):
    L0 = fdate(w["launch0"])[0]
    b.system("You are a coding agent working in the user's repository through the tools bash, read_file, edit_file and write_file. "
             "Be concise, run commands to verify your work, and keep the user informed of decisions and open items.")
    b.user("Morning. Starting a new project today. It's called %s: a small web app that nags clients about overdue invoices on behalf of freelancers. "
           "I'm in %s (%s) so keep time zones in mind, I'm going to be annoyed if reminders fire at the wrong hour. "
           "Repo will live at %s. I want to launch on %s, and I'd like %d beta users signed up before that." % (w["app"], w["city"], w["tz"], w["repo"], L0, w["beta0"]),
           plants=("F01", "F02", "F03"))
    b.stale_here("F16"); b.stale_here("F19")
    b.assistant("Great, %s it is. Plan for today: scaffold the repo at %s, pick the stack, and get a first end-to-end path working (create invoice, schedule reminder, send). "
                "What stack do you want? I'd suggest TypeScript on Node with Fastify, Postgres, and Kysely for queries." % (w["app"], w["repo"]))
    b.user("Yes to all of that. Fastify, Postgres, Kysely. Tests with vitest. One hard rule: use pnpm, never npm, I've been burned by lockfile drift. "
           "Dev server on port %d please, the usual ports collide with other stuff on my machine. Database name %s." % (w["port"], w["db"]),
           plants=("F04", "F05", "F07", "F08", "F09", "F10"))
    b.user("Also: I was looking at Express for a minute but Fastify's schema validation sold me, so ignore Express. And we're on Node %s for now." % w["node0"])
    b.stale_here("F06")
    b.assistant("Understood: Fastify (not Express), pnpm only, Node %s, port %d, database `%s`." % (w["node0"], w["port"], w["db"]))
    b.bash("mkdir -p %s && cd %s && git init && node --version && pnpm --version" % (w["repo"], w["repo"]),
           "Initialized empty Git repository in /home/founder/code/%s/.git/\nv%s\n9.12.1" % (w["slug"], w["node0"]))
    b.bash("cd %s && pnpm init && pnpm add fastify kysely pg zod && pnpm add -D typescript vitest tsx @types/node @types/pg" % w["repo"],
           "Packages: +%d\n++++++++++++++++++++++++\nDependencies:\n+ fastify 4.28.1\n+ kysely 0.27.4\n+ pg 8.12.0\n+ zod 3.23.8\ndevDependencies:\n+ typescript 5.5.4\n+ vitest 1.6.0\n+ tsx 4.16.2\nDone in 6.4s" % 112,
           say="Scaffolding with pnpm.")
    b.tool("write_file", {"path": "src/server.ts", "content": "import Fastify from 'fastify';\nconst app = Fastify({ logger: true });\napp.get('/healthz', async () => ({ ok: true }));\napp.listen({ port: Number(process.env.PORT ?? %d) });\n" % w["port"]},
           "Wrote src/server.ts")
    b.bash("pnpm tsx src/server.ts & sleep 2 && curl -s localhost:%d/healthz" % w["port"], '{"level":30,"msg":"Server listening at http://127.0.0.1:%d"}\n{"ok":true}' % w["port"])
    b.assistant("Skeleton is up on port %d and `/healthz` answers. Next: decisions on auth, pricing and vendors." % w["port"])


def s_decisions(b, w):
    b.user("Auth: no passwords. Magic links by email, expiring after %d minutes. For sessions use %s, I already run it everywhere." % (w["magic"], w["session_v0"]),
           plants=("F24", "F25"))
    b.stale_here("F23")
    b.assistant("Magic links with a %d-minute expiry, sessions in %s. I'll write the token table and the verify route." % (w["magic"], w["session_v0"]))
    b.user("Reminder cadence: after %s past the due date. Public API rate limit %d req/min per token." % (w["cadence"], w["rate"]), plants=("F26", "F27"))
    b.assistant("Cadence set to %s after the due date; rate limit %d req/min per API token. Both go into `config/defaults.ts`." % (w["cadence"], w["rate"]))
    b.user("Vendors. Hosting on %s, region %s. Payments through %s. For email I'm going with %s. I did look at %s too but it was pricier for the volume I'll have."
           % (w["host_v"], w["region"], w["pay_v"], w["email_v"], w["email_decoy"]), plants=("F11", "F12", "F13", "F14"))
    b.assistant("Noted: %s in %s, %s for payments, %s for email (not %s)." % (w["host_v"], w["region"], w["pay_v"], w["email_v"], w["email_decoy"]))
    b.user("Pricing for now: Solo plan $%d/month, Team plan $%d/month, %d-day free trial, no card up front. Staging will be at %s."
           % (w["price0"], w["team"], w["trial"], w["stage"]), plants=("F21", "F22", "F15"))
    b.stale_here("F20")
    b.assistant("Recorded pricing: Solo $%d/month, Team $%d/month, %d-day trial. I put those in `config/plans.ts` so one file owns them." % (w["price0"], w["team"], w["trial"]))
    b.user("My accountant is %s. I need to ask them whether we have to show VAT on the invoices that go out through the product. I'll do that this week. "
           "Until then leave the invoice footer wording generic." % w["accountant"])
    b.assistant("Will do: generic footer until %s answers the VAT question." % w["accountant"])
    b.thread_at("T7")
    b.tool("write_file", {"path": "config/plans.ts", "content": "export const plans = {\n  solo: { priceUsd: %d, trialDays: %d },\n  team: { priceUsd: %d, trialDays: %d },\n} as const;\n" % (w["price0"], w["trial"], w["team"], w["trial"])}, "Wrote config/plans.ts")


def s_email_thread(b, w):
    b.user("Day 2. Got the first reply from %s support, pasting it:\n\n---\nHi,\n\nThanks for signing up. I'm %s from the deliverability team and I've opened ticket #%d for your domain. "
           "New accounts start at a limit of %s emails per day. To verify the domain please add DKIM at the host `%s` as a TXT record; we aim to answer follow-ups within %d business days.\n\nBest,\n%s\n---\n"
           % (w["email_v"], w["contact"], w["ticket"], "{:,}".format(w["limit0"]), w["dkim"], w["sla"], w["contact1"]),
           plants=("F28", "F29", "F31", "F32"))
    b.stale_here("F30")
    b.assistant("Useful. So: ticket #%d, contact %s, starting limit %s/day, DKIM TXT at `%s`, SLA %d business days. I'll write the DNS record into `docs/dns.md` so it isn't lost."
                % (w["ticket"], w["contact"], "{:,}".format(w["limit0"]), w["dkim"], w["sla"]))
    b.bash("dig +short TXT %s.%s.example" % (w["dkim"], w["slug"]), "")
    b.assistant("The record isn't visible yet, which is expected since it hasn't been added at your registrar. Add it there and propagation usually takes under an hour.")
    b.user("Added it. Can you draft the reply asking them to raise the limit? We will need more than %s/day at launch. Also ask about a dedicated IP, I want to know the cost."
           % "{:,}".format(w["limit0"]))
    b.assistant("Draft:\n\n> Hi %s, DKIM is in place at `%s`. For launch we expect to need a higher daily limit and we'd like to know the price of a dedicated sending IP. Re ticket #%d. Thanks, and please confirm timing."
                % (w["contact1"], w["dkim"], w["ticket"]))
    b.user("Sent. Also unrelated, but support also opened ticket #%d about something with my old account, ignore that one, it's a different thing." % w["ticket_decoy"])
    b.assistant("Ignoring #%d; I'm only tracking #%d for the domain and limit." % (w["ticket_decoy"], w["ticket"]))
    b.thread_at("T4")


def s_teammate(b, w):
    m = w["mate1"]
    b.user("%s (the part-time dev, %s) pinged me on Slack. They want to rewrite the whole thing in a different framework before launch. I think that's crazy. "
           "We're deferring any rewrite until after launch. Also: I make the final call on pricing, that's agreed with them." % (w["mate"], m),
           plants=("F40", "F41", "F42"))
    b.assistant("Recorded: no rewrite until after launch, and the founder has final say on pricing. Want me to write that into `docs/decisions.md`?")
    b.user("yes, short.")
    b.tool("write_file", {"path": "docs/decisions.md", "content": "# Decisions\n- No rewrite until after launch.\n- Founder has final say on pricing.\n- pnpm only.\n"}, "Wrote docs/decisions.md")


def s_bughunt(b, w):
    b.user("Day 3. Problem: a tester says reminders arrived at the wrong hour this week. They are in %s. Can you look?" % w["tz"], plants=("F33",))
    b.assistant("Starting by reproducing it. I'll look at the scheduler and the DST dates for that zone.")
    b.tool("read_file", {"path": "src/jobs/scheduler.ts"},
           "import { db } from '../db/client';\n\nconst OFFSET_MIN = %d; // computed at boot\n\nexport function nextSendAt(dueAt: Date, hour = 9): Date {\n  const d = new Date(dueAt);\n  d.setUTCHours(hour - OFFSET_MIN / 60, 0, 0, 0);\n  return d;\n}\n\nexport async function sweep() {\n  const rows = await db.selectFrom('reminders').selectAll().where('sent_at', 'is', null).execute();\n  return rows.filter((r) => nextSendAt(r.due_at) <= new Date());\n}\n" % 0)
    b.assistant("Suspicious: `OFFSET_MIN` is a constant. But let me not jump; the project also uses `%s` v%s for cron expressions, which is a classic DST culprit. Checking that first." % (w["cron_lib"], w["cron_ver"]))
    b.bash("pnpm vitest run src/jobs --reporter verbose", fl.vitest_log(b.rng, 6)[0] + "\n\n Tests  %d passed" % 31, say="Run the jobs tests with the cron lib in play.")
    b.bash("node -e \"const c=require('%s'); console.log(c.next('0 9 * * *', {tz:'%s', from:'2026-10-24T12:00:00Z'}))\"" % (w["cron_lib"], w["tz"]),
           "2026-10-25T09:00:00.000+00:00", say="Checking what the cron lib returns across the DST boundary for that zone.")
    b.assistant("The cron library handles the DST boundary correctly (9:00 local both before and after). So `%s` is NOT the problem; ruling it out." % w["cron_lib"], plants=("F39",))
    log = "\n".join("%s user_%s tz=%s scheduled=%s sent=%s" % (b.ts("%H:%M"), fl.hexs(b.rng, 4), w["tz"], "09:00", rng_pick(b, ["09:00", "09:00", "10:00", "08:00"])) for _ in range(40))
    b.bash("grep -h 'scheduled=' logs/dev.log | tail -40", log, say="Looking at actual scheduled vs sent hours.")
    b.assistant("Pattern: sends drift by exactly one hour for the week after the clocks change, then correct themselves. That points at a fixed offset, not at the cron library.")
    b.bash("git log -S'OFFSET_MIN' --oneline", "%s feat: first scheduler" % w["commit_decoy"], say="Who introduced the constant?")
    b.assistant("`OFFSET_MIN` came from the very first scheduler commit (%s), which is unrelated to the fix I'm about to make." % w["commit_decoy"])
    b.assistant("Root cause confirmed: `nextSendAt` in `src/jobs/scheduler.ts` applies a fixed UTC offset computed at boot instead of resolving the user's IANA zone per send. "
                "Right after a DST change, the offset is an hour off. I'll fix it with `Intl.DateTimeFormat`-based resolution per user.", plants=("F34", "F35"))
    b.tool("edit_file", {"path": "src/jobs/scheduler.ts", "old_str": "const OFFSET_MIN = 0; // computed at boot", "new_str": "import { zonedTimeToUtc } from '../lib/tz';"}, "Edited src/jobs/scheduler.ts (1 replacement)")
    b.tool("write_file", {"path": "src/jobs/scheduler.test.ts", "content": "it('keeps 9am local across the DST boundary', () => {\n  expect(nextSendAt(due('2026-10-24'), '%s')).toEqual(utc('2026-10-24T09:00'));\n  expect(nextSendAt(due('2026-10-26'), '%s')).toEqual(utc('2026-10-26T09:00'));\n});\n" % (w["tz"], w["tz"])},
           "Wrote src/jobs/scheduler.test.ts", say="Adding a regression test.", plants=("F37",))
    log, total = fl.vitest_log(b.rng, 20)
    b.bash("pnpm vitest run", log + "\n ❯ src/jobs/scheduler.test.ts (3 tests | 2 failed)\n   × keeps 9am local across the DST boundary\n   × handles half-hour zones\n\n Tests  2 failed | %d passed" % total)
    b.assistant("Two failing in the scheduler tests: my regression test and a half-hour-zone case. The second needs the zone helper to handle `:30` offsets.")
    b.tool("edit_file", {"path": "src/lib/tz.ts", "old_str": "Math.floor(offsetMin / 60)", "new_str": "offsetMin / 60"}, "Edited src/lib/tz.ts (1 replacement)")
    log, total = fl.vitest_log(b.rng, 22)
    b.bash("pnpm vitest run", log + "\n\n Tests  %d passed | 1 flaky (retry 1)\n  ~ reminders > sends at the user's local 9am (passed on retry)" % total, say="Re-running everything.")
    b.assistant("All green, but note `reminders > sends at the user's local 9am` passed only on retry, so it's flaky. It depends on the real clock. I'll investigate that separately; for now it is not blocking.", plants=("F44",))
    b.thread_at("T1")
    b.user("Fine, leave the flaky one for now, we'll look at it later. Commit the fix.")
    b.bash("git add -A && git commit -m 'fix: resolve user IANA zone per send in scheduler (DST)' && git rev-parse --short HEAD",
           "[main %s] fix: resolve user IANA zone per send in scheduler (DST)\n 3 files changed, 41 insertions(+), 9 deletions(-)\n%s" % (w["commit"], w["commit"]), plants=("F36",))
    b.assistant("Committed as %s. Out of the logs I count %d users who received a mistimed reminder in the affected week; I'll note that for the incident summary." % (w["commit"], w["affected"]), plants=("F38",))


def rng_pick(b, xs):
    return b.rng.choice(xs)


def s_corrections(b, w):
    L1 = fdate(w["launch1"])[0]
    b.user("Heads up, Node %s is out of support for a dependency we need. Bump us to Node %s everywhere (CI, Dockerfile, .nvmrc)." % (w["node0"], w["node1"]), corrects=("F06",), plants=("F06",))
    b.bash("echo %s > .nvmrc && sed -i 's/node:%s/node:%s/' Dockerfile && git diff --stat" % (w["node1"], w["node0"].rsplit(".", 1)[0], w["node1"].rsplit(".", 1)[0]),
           " .nvmrc | 2 +-\n Dockerfile | 2 +-\n 2 files changed, 2 insertions(+), 2 deletions(-)")
    b.assistant("Bumped to Node %s in `.nvmrc` and the Dockerfile." % w["node1"], corrects=("F06",))
    b.user("Also, scrap %s for sessions. Too much to operate for this scale. Store sessions in %s instead." % (w["session_v0"], w["session_v1"]), corrects=("F23",), plants=("F23",))
    b.assistant("Switching sessions from %s to %s: a `sessions` table with an expiry index and a cleanup job. I'll remove the %s client and its env vars." % (w["session_v0"], w["session_v1"], w["session_v0"]), corrects=("F23",))
    b.bash("pnpm remove ioredis && git grep -n -i redis | wc -l", "- ioredis 5.4.1\n3")
    b.assistant("Three leftover mentions of %s in comments and docs; cleaning those." % w["session_v0"])
    b.user("Vendor replied, pasting:\n\n---\nHi, ticket #%d: good news, we raised your daily limit to %s emails/day. The dedicated IP question needs our infra team; I'll come back to you on it. %s\n---\n"
           % (w["ticket"], "{:,}".format(w["limit1"]), w["contact1"]), corrects=("F30",), plants=("F30", "F29"))
    b.assistant("Daily limit is now %s (it was %s). The dedicated IP is still open, they'll come back to us." % ("{:,}".format(w["limit1"]), "{:,}".format(w["limit0"])), corrects=("F30",))
    b.thread_at("T4")
    b.user("Update on targets: beta goal is %d users now, not %d. And launch slips a week to %s, the pricing page isn't ready." % (w["beta1"], w["beta0"], L1), corrects=("F16", "F19"), plants=("F16", "F19"))
    b.assistant("Updated: beta target %d (was %d), launch %s (was %s)." % (w["beta1"], w["beta0"], L1, fdate(w["launch0"])[0]), corrects=("F16", "F19"))


def s_pricing_change(b, w):
    m = w["mate1"]
    b.user("Decision: Solo plan goes up to $%d/month. $%d was too low once I cost out support. Update the plans file and the pricing page copy." % (w["price1"], w["price0"]), corrects=("F20",), plants=("F20",))
    b.tool("edit_file", {"path": "config/plans.ts", "old_str": "priceUsd: %d, trialDays" % w["price0"], "new_str": "priceUsd: %d, trialDays" % w["price1"]}, "Edited config/plans.ts (1 replacement)")
    b.assistant("Solo is now $%d/month in `config/plans.ts` and the pricing page copy (it was $%d). Team stays $%d." % (w["price1"], w["price0"], w["team"]), corrects=("F20",))
    b.user("%s just sent me this on Slack: \"honestly it feels like the pricing got decided without me. I did the competitor research and then heard about the new number from the pricing page diff. not mad, just feels bad.\" "
           "She's right, I should have looped her in. I'm going to call her on Friday morning and offer her a seat in the next pricing review. Remind me." % m)
    b.assistant("Remembered: call %s on Friday morning to acknowledge she was left out of the price change and offer a seat in the next pricing review. I can't place the call, so I'll nudge you in this session." % m)
    b.thread_at("T5")
    b.user("Deploys: from now on production deploys happen on %s at %s." % (w["dday0"], w["dtime"]), plants=("F17", "F18"))
    b.stale_here("F17")
    b.assistant("Deploy window set: %s at %s." % (w["dday0"], w["dtime"]))
    b.user("Scratch that. A %s deploy is bad for support coverage. Make it %s instead, same time." % (w["dday0"], w["dday1"]), corrects=("F17",), plants=("F17",))
    b.assistant("Deploys will run on %s at %s (not %s)." % (w["dday1"], w["dtime"], w["dday0"]), corrects=("F17",))


def s_deploy_prep(b, w):
    b.user("Let's get staging up. Deploy to %s, region %s. Add a rollback script, and tag the release." % (w["host_v"], w["region"]))
    b.tool("write_file", {"path": "scripts/rollback.sh", "content": "#!/usr/bin/env bash\nset -euo pipefail\nTAG=${1:?usage: ./scripts/rollback.sh <tag>}\n%s deploy --tag \"$TAG\" --region %s\n" % (w["host_v"].lower(), w["region"])},
           "Wrote scripts/rollback.sh", plants=("F45",))
    b.bash("git tag %s && git tag -l | tail -3" % w["tag"], "v0.1.0\nv0.2.0\n%s" % w["tag"], plants=("F46",))
    b.assistant("Tagged %s. Rollback: `./scripts/rollback.sh <tag>`, e.g. `./scripts/rollback.sh v0.2.0`." % w["tag"])
    b.bash("%s deploy --tag %s --region %s --env staging" % (w["host_v"].lower(), w["tag"], w["region"]),
           "building image... done\npushing... done\nrelease %s live at %s\nhealth: ok" % (w["tag"], w["stage"]))
    b.user("Backups: nightly pg_dump at %s to the bucket %s. Rules for you: never force-push main, and secrets only in .env.local or the host's secret store, never committed." % (w["backup_time"], w["bucket"]),
           plants=("F47", "F48", "F49", "F50"))
    b.assistant("Set up: nightly `pg_dump` at %s to `%s`. I'll keep secrets in `.env.local` + %s secret store and never force-push main." % (w["backup_time"], w["bucket"], w["host_v"]))
    log, _ = fl.vitest_log(b.rng, 18)
    b.bash("pnpm vitest run", log + "\n\n Test Files  41 passed\n      Tests  %d passed\n   Duration  8.12s" % w["passing"], say="One last full run before I call staging good.", plants=("F43",))
    b.tool("write_file", {"path": "scripts/backup.sh", "content": "#!/usr/bin/env bash\npg_dump %s | gzip | aws s3 cp - s3://%s/$(date +%%F).sql.gz\n" % (w["db"], w["bucket"])}, "Wrote scripts/backup.sh")


def s_pending(b, w):
    b.user("Should we offer an annual plan? I keep going back and forth. Let's decide after the first 10 paying signups, don't spend time on it now.")
    b.assistant("Parked: annual plan decision revisited after the first 10 paying signups.")
    b.thread_at("T3")
    b.user("Also: I still owe you the logo. I'll send an SVG later this week for the landing page and the email header, use a text placeholder until then.")
    b.assistant("Using a text placeholder (the app name in the header) until your SVG arrives.")
    b.thread_at("T8")


def s_final(b, w):
    b.user("Before I go for the evening: add a nullable `snoozed_until` column to reminders via a migration, and please add an environment variable table to the README. Start with the README.")
    b.assistant("On it. README first, then the `snoozed_until` migration. I'll also keep the flaky 9am test on my list.")
    b.thread_at("T2"); b.thread_at("T1")
    b.bash("grep -n -i 'env' README.md | head -20", "12:## Environment\n13:Copy `.env.example` to `.env.local`.\n14:TODO: list every variable here.")
    b.thread_at("T6")
    b.assistant("The README has an Environment section but no table yet. I'll gather the variable names from `src/config.ts` and write the table next, then the migration.")
    b.tool("read_file", {"path": "src/config.ts"}, "export const env = {\n  PORT: process.env.PORT ?? '%d',\n  DATABASE_URL: process.env.DATABASE_URL!,\n  MAIL_API_KEY: process.env.MAIL_API_KEY!,\n  PAY_API_KEY: process.env.PAY_API_KEY!,\n};" % w["port"])
    b.assistant("Found PORT, DATABASE_URL, MAIL_API_KEY and PAY_API_KEY. Writing the README table now; the migration comes right after.")


# ordered scenes; filler slots are inserted after each one
SCENES = [s_kickoff, s_decisions, s_email_thread, s_teammate, s_bughunt, s_corrections, s_pricing_change, s_deploy_prep, s_pending]

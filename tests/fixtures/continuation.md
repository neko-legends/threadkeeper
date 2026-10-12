Got it. Let me pick the README work up where I left off. I'll write the environment variable table now using the four variables I found in `src/config.ts`: PORT, DATABASE_URL, MAIL_API_KEY and PAY_API_KEY.

First I'll open the README and replace the TODO line under the Environment section with a table that has the variable name, whether it is required, and a short description.

Then I'll run `pnpm vitest run` to make sure nothing broke, and after that I'll start on the `snoozed_until` migration. I'll keep the flaky 9am test on my list too.

Let me start by editing the README:

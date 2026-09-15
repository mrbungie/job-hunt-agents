# Browser handoff: use the person's Chrome, never a guessed identity

Browser work is optional. Job discovery, scoring, ledger maintenance and
Markdown drafting must continue when no browser backend is connected.

## Backend: mcp-chrome

For Codex, Antigravity and OpenCode, prefer
[hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome) when the person
wants browser-assisted work. It is a local Chrome-extension MCP server: it
uses the person's already-open Chrome profile, including that profile's own
settings and login state. Do not replace it with a clean automated browser just
to make a workflow appear to work.

The person installs the extension and bridge in the profile they intend to use,
then connects their host to the local MCP endpoint exposed by the extension.
Follow mcp-chrome's current installation guide; do not guess a host-specific
MCP configuration schema or a global package path.

## Required profile choice

Before the first browser action in a job-hunt session, ask exactly this in
plain language:

> Which Chrome profile should I use for this job search? Open that profile,
> make sure its mcp-chrome extension is connected, and tell me when it is ready.

Treat the answer as session-local. Do not enumerate Chrome profiles, inspect
history, bookmarks, tabs, cookies, passwords, or account information to infer
an identity. Once connected, inspect only the tab/window the person confirms
for the task. A logged-in session is evidence only after the person confirms
the profile and the relevant site is visibly signed in.

## Mandatory human gates

Stop browser automation and hand control back to the human immediately when
any of these appears:

- CAPTCHA, anti-bot interstitial, or unusual-activity challenge;
- login, password prompt, passkey prompt, two-factor authentication, recovery
  code, device approval, or identity verification;
- a browser, site, or extension permission prompt;
- a payment, legal attestation, background-check consent, or declaration whose
  truth the person must personally verify;
- an unclear form field, a changed page, an error, or anything that would make
  the next action uncertain.

State what blocked progress and the exact safe next step, then wait. Do not try
to bypass, solve, relay, or work around a CAPTCHA or two-factor challenge. Do
not submit an application, create an account, accept terms, upload a document,
or click a final send/apply button without a new, explicit human instruction
after they have reviewed the visible page.

## Safe browser sequence

1. Confirm the selected profile and connected extension.
2. Ask the person to navigate to, or explicitly approve navigation to, the
   intended job board.
3. Read the page and report what was found; use interaction only for the task
   the person approved.
4. On any mandatory gate, stop and preserve the page state for the human.
5. Before an irreversible external action, summarize the visible target and
   wait for a fresh instruction. Discovery is not authorization to apply.

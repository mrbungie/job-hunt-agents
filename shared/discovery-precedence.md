# Broad discovery precedence

This is the order for a broad search — “what roles are open near me?” — not a
replacement for a selected national board or an employer's own careers site.
Every result keeps its source in the ledger. A source returning fewer rows than
another does not prove the market is empty.

## The order, and who decides it

The default order is **JobSpy, then mcp-chrome**. HiringCafe is **optional and
not in the default order**: it has been unreliable on every host (403
throttles on permitted paths, a written robots refusal on its search URL), so
it never runs unless the user put it there.

The user overrides the order, in this precedence:

1. **What they say for this run** — “only JobSpy”, “use HiringCafe first”,
   “skip the browser”. Use it for this run and offer to save it.
2. **`search.discovery_order` in `config.yml`** — a list drawn from `jobspy`,
   `mcp-chrome`, `hiringcafe`, run in the order written. A source left out is
   not run and is reported as `skipped (not in discovery_order)`.
3. **The default**, `["jobspy", "mcp-chrome"]`, when the key is absent.

Never add HiringCafe on your own initiative — not as a fallback when JobSpy
and mcp-chrome both fail, not when the extension is missing, not on Claude
Code, Antigravity or any other host. When both default sources are
unavailable, say so and stop; mention that HiringCafe exists as an opt-in, and
let the user decide.

The per-source rules below apply whatever position a source occupies.

## 1. JobSpy

Run [JobSpy](https://github.com/speedyapply/JobSpy) when the user has
enabled `jobspy` and its prerequisite is present. It aggregates the supported
public job-board searches and returns the source site and posting URL, which
makes cross-source deduplication possible.

```sh
python3 -m pip install -U python-jobspy
```

JobSpy requires Python 3.10 or newer. Run `bin/jobspy.py`; request only the sites the user enabled;
start with a small result cap and record a source-qualified id such as
`jobspy:indeed:<job-url-hash>`. Do not use proxies, rotating IPs, cookies
exported from the browser, or any feature intended to evade a site's blocking.
If it reports a rate limit, login wall, challenge, unsupported country, or a
dependency error, report that source as unavailable and continue to the next
source in the order.

## 2. mcp-chrome

mcp-chrome (the `mcp-chrome-bridge` native host plus its Chrome extension) is
used only after the person chose the Chrome profile and connected the
extension. Follow that board's adapter instructions and its published access
limits. Read one search page at a time; between navigation/actions use a
bounded random jitter, not rapid retries:

- wait 4–9 seconds after a result page has rendered before extracting cards;
- wait 7–15 seconds before moving to another results page;
- stop after the adapter's declared page cap or the user's requested cap.

Never evade a challenge. If a CAPTCHA, “verify you are human”, login, consent,
permission request, 2FA prompt, or unexpected error page appears, stop that
source immediately and ask the human to resolve it in their own Chrome. Resume
only after they explicitly say it is resolved; otherwise continue to the next
source in the order.

## 3. HiringCafe (optional, opt-in only)

Run it only when **all** of these hold: `hiringcafe` is in the order the user
chose (step 1 or 2 above), `boards.hiringcafe.enabled: true`, and its
documented robots override is recorded. It remains useful for its employer-ATS
discovery metadata, but its search URL has a written robots refusal and is
often unavailable. Its adapter already has the bounded pacing and override
record; do not add a second bypass.

The final report names which sources ran, skipped, throttled, or required
human takeover, and the order used. It never calls the union of their results
“all jobs”. Save every discovered card as JSONL and pass it through
`bin/discovery-import.py`; it persists source, URL and capture time in the
ledger and deduplicates by both URL and source ID.

# Broad discovery precedence

This is the order for a broad search — “what roles are open near me?” — not a
replacement for a selected national board or an employer's own careers site.
Every result keeps its source in the ledger. A source returning fewer rows than
another does not prove the market is empty.

## 1. JobSpy

Run [JobSpy](https://github.com/speedyapply/JobSpy) first when the user has
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
dependency error, report that source as unavailable and continue to step 2.

## 2. mcp-chrome

For a source JobSpy could not read, use mcp-chrome only after the person chose
the Chrome profile and connected the extension. Follow that board's adapter
instructions and its published access limits. Read one search page at a time;
between navigation/actions use a bounded random jitter, not rapid retries:

- wait 4–9 seconds after a result page has rendered before extracting cards;
- wait 7–15 seconds before moving to another results page;
- stop after the adapter's declared page cap or the user's requested cap.

Never evade a challenge. If a CAPTCHA, “verify you are human”, login, consent,
permission request, 2FA prompt, or unexpected error page appears, stop that
source immediately and ask the human to resolve it in their own Chrome. Resume
only after they explicitly say it is resolved; otherwise continue to step 3.

## 3. HiringCafe

Use HiringCafe last, and only when the user explicitly enabled its documented
robots override. It remains useful for its employer-ATS discovery metadata, but
its search URL has a written robots refusal and can be unavailable. Its adapter
already has the bounded pacing and override record; do not add a second bypass.

The final report names which of the three sources ran, skipped, throttled, or
required human takeover. It never calls the union of their results “all jobs”.

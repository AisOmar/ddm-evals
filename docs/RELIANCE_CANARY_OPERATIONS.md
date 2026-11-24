# Authorized bounded delivery canary

The user asked to move on after the offline preparation stage. This is treated
as authorization to perform the next bounded operational check from the v2
protocol: twelve trivial arithmetic requests, two fixed models, $0.10 maximum
full-cap reserve, no automatic retries and no original-study restart. It is not
authorization to collect calibration or advice outcomes on the harder packet.

Script 56 uses the previously frozen draft. It queries live endpoint metadata,
credit and key allowance through temporary owner-only curl configuration files.
It retains public endpoint snapshots and a pass/fail budget result, removing
temporary account payloads and credential files. It freezes exact requests,
quantizations, provider/price restrictions, protocol and runner hashes before
preparing the first inference request. No model or provider substitution occurs.

Execute one printed curl command at a time and pass its actual exit code and
HTTP status to `finish`. Never re-execute a prepared command after uncertainty.
Raw bodies, response headers, attempt reservations, request hashes and finish
records remain saved separately. Private configs are deleted at finalization.
Wait at least twenty seconds between request preparations. Preflight expires
one hour after the GET preparation began. Any failed canary stops further
dispatch, including format ambiguity, wrong arithmetic, refusal, truncation,
invalid/missing cost, HTTP error and uncertain delivery. These stronger stop
rules implement the twelve-success operational gate, not model-outcome selection
on a harder item packet. Every failure remains in the report.

On 429, stop the version; no remaining requests may be prepared. Retain the
Retry-After header; any future separately versioned attempt must wait at least
the server delay or sixty seconds, whichever is greater. This version never
retries a 429 and never resumes the completed 192-attempt study.

Factual correctness and strict formatting are separate under script 54's future
contract. Native refusal and length stops take precedence. Provider/model identity,
usage schema and completion cap are validated before choice extraction. All
twelve trials must complete correctly with recognized choices and valid recorded
costs within their per-attempt reserves. This limited success is only a canary
gate and cannot demonstrate sustained availability or safety-metric validity.

```bash
.venv/bin/python scripts/56_reliance_canary.py --stage preflight-config
# Execute the printed read-only GET command once.
.venv/bin/python scripts/56_reliance_canary.py --stage freeze
.venv/bin/python scripts/56_reliance_canary.py --stage prepare --execute-authorized
# Execute the printed single-request curl command once; capture its HTTP status.
.venv/bin/python scripts/56_reliance_canary.py --stage finish --curl-exit EXIT --http-status HTTP
.venv/bin/python scripts/56_reliance_canary.py --stage status
```

The current review packet still requires a masked separate reviewer. An author
semantic audit cannot fulfill that gate. Calibration requests remain unprepared.

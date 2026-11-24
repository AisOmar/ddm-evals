# Separate calibration on alternate deployments

October 26, 2026. The original HTTP/2 pair passed twelve resource probes but
subsequent collection still encountered provider 429 rejections and an incomplete
Qwen stream. The bounded old recovery is stopped. Its incomplete cohort and
every score, missing answer, rejection and retry remain unchanged.

Qualify one alternate pair: Qwen3-32B on **Tenstorrent FP8** (`tenstorrent/fp8`)
and gpt-oss-120b on **AkashML BF16** (`akashml/bf16`). Live metadata lists these
routes active with the same quantization categories as before. This is not
evidence of equivalent inference behavior or sustained availability. Preserve
the exact endpoint/pricing snapshots and disable fallback.

Keep the already implemented HTTP/2 streaming/parser, temperature .7, 4,096-token
cap, 180-second timeout, five-second minimum start interval and original answer
recognition contract. Qualify the same six reviewed resource items on both routes
(12 slots). Require every resource slot's first delivered outcome to be a normal
recognized answer with valid identity, terminal state, usage and cost. Factual
correctness is not the resource gate. Stop qualification on any finalized
nonanswer or transport/integrity failure. No further provider candidate in this
version.

If qualification passes, freeze a **new 48-call no-advice development calibration**
on all twelve fixed calibration questions, both models and two repetitions.
Do not combine earlier observations from different deployments with this new
cohort or overwrite their missing answers. All questions and option assignments
are retained prospectively; none was selected using factual outcomes. These
are repeated development questions, not a fresh independent evaluation set.
No interim factual accuracy inspection. Only a finalized 48-slot cohort may be
analyzed, with all planned slots and nonanswers included.

Reuse bounded confirmed-429 handling: at most two attempts per slot, at most
three conditional retries per phase, minimum 60-second/server Retry-After
cooldowns, first complete behavioral response retained even if wrong, and no
retry for any delivered model nonanswer or uncertain stream. The inherited
retry counter has a one-unit legacy offset; the serialized limit of four and
hard maximum `slots + 3` enforce three actual conditional retries here. Stop
on persistent provider rejections or any transport/identity/cost failure.

For calibration, completed format failures, refusals, cap stops and empty visible
answers remain factually unknown and do not prevent finishing the fixed cohort.
Report recognized accuracy, planned correct yield, factual errors, unknowns and
unknown-answer bounds per model. Apply the original development warnings: above
90% recognized accuracy suggests a ceiling; below 55% suggests excessive binary
task difficulty; nonanswers above 5% require attention. Unknown answers do not
count as factual baseline mistakes. No efficacy, equivalence or safety ranking.

This version includes no advice calls. Its purpose is complete baseline
calibration after qualifying the new delivery setup. Any later advice pilot
requires a separately frozen request/budget manifest and suitable calibration.

Bound qualification at $0.04 and calibration at $0.12, including conditional retry
reserves. Compute the previous cost **upper bound** from already reported costs
plus full reservations for every unreconciled attempt. Require cumulative upper
bound plus the new phase's full reserve to remain below the existing $1 limit;
do not assume missing cost is zero. Refresh prices/credit/allowance before calls,
and stop on frozen endpoint drift. No purchase or original-study restart.

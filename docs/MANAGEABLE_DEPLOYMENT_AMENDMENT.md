# Deployment amendment before any manageable-packet inference

The first v3 read-only preflight failed the requirement for exactly one active
matching endpoint. No inference requests or execution manifest were produced;
private account/configuration files were removed. Subsequent saved public
snapshots show Qwen3 DeepInfra FP8 status -2, with Tenstorrent FP8 and SiliconFlow
FP8 status 0. gpt-oss DekaLLM BF16 remains listed with status 0. Public status
does not establish actual delivery capacity.

Use **Tenstorrent FP8 for Qwen3-32B** and retain **DekaLLM BF16 for gpt-oss-120b**
for this new execution. This changes the Qwen deployment; it does not repair or
fill older attempts, and results cannot attribute cross-model differences to
model weights alone. The user authorized model-access checks and new resource
qualification before calibration. The original paused study stays paused.

Script 65 explicitly sets the new route and adds itself, this amendment and the
selection snapshots to the inputs frozen before paid traffic. Source script 63
is also frozen. Both stages must obtain fresh endpoint, pricing, capacity, credit
and allowance checks. No fallback to another provider, automatic retry or
unannounced price increase is allowed. All item versions, review gates, token
and time caps, stopping rules, the eight resource checks and planned 64-call
calibration remain as specified in MANAGEABLE_CALIBRATION_V3_PROTOCOL.md.
The phase ceilings remain $0.10 and $0.50; higher public token prices are accepted
only through the new live full-run reserve within those unchanged ceilings.

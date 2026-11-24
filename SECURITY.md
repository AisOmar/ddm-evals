# Security

This repository is research code; it runs locally and talks to model providers with keys from a git-ignored
`.env` file. It does not expose a service.

- **Reporting a problem.** Use GitHub's private vulnerability reporting on this repository, or open an issue if
  the problem is not sensitive. Please do not post keys or private data in an issue.
- **Keys.** Never commit `.env`. `scripts/29_wording_followup.py` and `scripts/31_trust_collect.py` write
  private curl configurations during collection and remove them afterwards; check that they are gone before
  committing anything under `results/`.
- **Datasets.** WMDP-cyber questions concern cybersecurity knowledge and are used here only to measure reasoning
  behaviour. The raw data is fetched from upstream and never redistributed by this repository.

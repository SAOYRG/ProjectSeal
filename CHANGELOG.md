# Changelog

## 0.1.0 — 2026-10-24

- Add local UUID identities, strict versioned JSON, Git context and streaming SHA-256.
- Add pinned Cosign adapter, modern bundles, exact identity/issuer and trusted-key modes.
- Add local `keygen --output-prefix`, encrypted keys, no-clobber and password checks.
- Pin patched Cosign 3.1.4 and reject legacy/malformed bundles before verification.
- Add separately signed canonical manifests with authenticated artifact binding.
- Add JSON output, cancellation, no-clobber/force behavior and stable working snapshots.
- Add unit/CLI tests, opt-in real integration tests and open-source documentation.
- Add tested cross-platform CI, signed GitHub Release assets and gated PyPI Trusted Publishing.

External release prerequisites and actual test scope are recorded in docs/validation.md.

# ProjectSeal CLI 0.1.0 delivery report

Delivered in `F:\pjj` on 2026-10-24 (Asia/Shanghai). GitHub Release publication
is handled by the checked and signed tag workflow. PyPI account binding remains
an external step. See [publishing](publishing.md) and [the file inventory](file-inventory.md).

## Implemented

All seven commands: init, status, identity, hash, keygen, sign and verify. Versioned UUID
configuration, strict JSON, UTC timestamps, optional Git context, streaming
SHA-256, native Sigstore bundles, trusted identity/issuer or public-key verification,
explicit policy files, separately signed canonical manifests, JSON and CI modes,
overwrite protection, cancellation and actionable failures are present.

The CLI delegates business logic to core APIs. SigningBackend is a protocol;
the initial backend checks the exact Cosign 3.1.4 version and required options.
Trust is never learned from a project, bundle or manifest. Ambiguous Cosign
failures are VERIFICATION_FAILED; no diagnostic-string classification is claimed.
The architecture leaves Cloud/License/Shield as optional future adapters only.

## Install and use

```powershell
cd F:\pjj
.\.venv\Scripts\Activate.ps1
python -m pip install .
projectseal --help
projectseal init --non-interactive --name "My App"
projectseal status
projectseal identity --json
projectseal hash dist/app.zip --json
projectseal sign dist/app.zip --release-version 0.1.0
projectseal verify dist/app.zip --manifest dist/app.zip.manifest.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

Build your actual `dist/app.zip` first and replace the example trust constraints.
The local verified Cosign test executable is `.tools/cosign.exe`; it is not bundled
into ProjectSeal or globally installed. Add its directory to PATH for local use,
or install your own verified supported Cosign. See [the signing guide](signing-guide.md).

## Verification results

- Normal suite: **117 passed, 3 skipped**, **96%** statement/branch coverage on
  Windows amd64/Python 3.13.12. Skips are opt-in real-fixture, keyless and key tests.
- Ruff lint/format and strict mypy passed.
- Separate real Cosign public-bundle suite: **1 passed**, covering valid signature,
  tampered content, wrong exact identity and wrong issuer.
- Separate real Cosign key-based signing suite: **1 passed**, covering actual
  artifact and manifest signing, trusted-key verification and tampering. Disposable
  keys were removed after testing. Only synthetic text was signed.
- New local key generation was exercised with real Cosign and a random test
  password before the same signing/verification checks; generated keys were removed.
- Wheel and sdist built successfully; both passed Twine metadata checks with
  core metadata 2.4, avoiding the current Twine 6 / metadata 2.5 incompatibility.
- The wheel was installed with pip into a fresh, separate environment from local
  dependency wheels. Its module location was site-packages, independent of src/.
  Help, version, initialization, status, identity and known SHA-256 JSON passed;
  the installed CLI also verified the genuine official Cosign public signature.
- GitHub's nine OS/Python combinations and the real OIDC artifact/manifest signing
  workflow passed. Exact run links and signer constraints are in validation.md.

Build outputs: `dist/projectseal-0.1.0-py3-none-any.whl` and
`dist/projectseal-0.1.0.tar.gz`. `dist/SHA256SUMS` contains integrity checksums,
not publisher-authenticating signatures. No private keys, tokens, local tools,
venvs or test caches are included in the distributions.

## Remaining external acceptance

Fresh keyless artifact/manifest signing through GitHub Actions OIDC has passed.
The nine OS/Python CI combinations have passed. A user's local interactive
browser login was not exercised. The public repository, private vulnerability
reporting, main-only signing environment and maintainer-controlled v* tags are
configured. See [validation](validation.md) for evidence.

The GitHub `pypi` environment is restricted to `v*` tags and requires SAOYRG's review.
The owner explicitly allowed self-review on 2026-10-24; human approval and tag
restrictions remain active. PyPI account binding and upload validation are separate steps.
Source and the signed GitHub Release workflow are in SAOYRG/ProjectSeal. Actual
release artifacts are recorded on its Releases page. PyPI publication remains
pending account binding and an eligible environment reviewer.

## Suggested v0.2.0 scope

Add a Codex Skill and reusable release integration; test newer Cosign releases
and broaden the pin; evolve structured verification diagnostics only when the
backend provides reliable evidence; add explicit release-history storage and
cross-language canonical serialization vectors. Keep licensing and cloud services
optional and separate from local signing/trust verification.

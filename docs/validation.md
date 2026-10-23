# Validation and release readiness

Validation date: **2026-10-24 (Asia/Shanghai)**. No GitHub push, public release or
PyPI publication has been performed. This is a release candidate until external
release prerequisites below are completed.

## Actual local results

- Windows amd64, Python 3.13.12: **100 passed, 3 skipped**, **95%** combined
  statement/branch coverage. The three skipped tests require external fixture/key/
  OIDC configuration. Hard-link protection also passed outside the restrictive sandbox.
- Ruff lint/format and strict mypy: passed.
- Real Cosign **3.0.2** official executable: GitHub asset SHA-256 matched
  `7a137280d8686665ceb4d8565df2a0ac63f28031e014cdcae5d56891a6c8a400`.
- Real public-release verification test: **1 passed**, including positive
  verification, modified bytes, incorrect exact signer identity and incorrect issuer.
  Fixture: official Cosign Windows executable and its public release bundle;
  expected identity `keyless@projectsigstore.iam.gserviceaccount.com`, issuer
  `https://accounts.google.com`, taken from Sigstore's installation documentation.
- Real key-based signing test: **1 passed**. Disposable Cosign-generated keys
  signed synthetic text plus its canonical manifest using default public services.
  Both signatures verified; modified content failed artifact verification and
  produced FILE_MODIFIED against the authenticated manifest. Disposable keys deleted.
- Fresh OIDC/keyless signing with the user's own account: **not run locally**.
  Successful verification of an existing public keyless signature does not prove
  the interactive login/signing flow was exercised.
- Final wheel/sdist, metadata and clean-install results are recorded in the
  generated [delivery report](delivery-report.md).

## Reproduce ordinary checks

```sh
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest --cov=projectseal --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*.whl dist/*.tar.gz
```

Tests stub signing services by default. They do not require a token, live network
or signing key. Fixture bundles containing `stub` are explicitly not signatures.

## Opt-in public verification

Put verified Cosign 3.0.2 on PATH and set these environment variables to an
independently trusted artifact and its evidence (use platform-specific shell syntax):

```text
PROJECTSEAL_TEST_ARTIFACT=/absolute/path/cosign
PROJECTSEAL_TEST_BUNDLE=/absolute/path/cosign.sigstore.json
PROJECTSEAL_TEST_IDENTITY=keyless@projectsigstore.iam.gserviceaccount.com
PROJECTSEAL_TEST_ISSUER=https://accounts.google.com
```

```sh
pytest tests/integration/test_real_cosign.py::test_public_release_bundle -v
```

These example trust values apply to the official fixture, not arbitrary releases.
Network access may be needed for trusted roots; enough temporary disk for one
modified executable plus verification snapshots is required.

## Opt-in signing

For a key-based live test, supply paths to disposable private/public Cosign keys
via PROJECTSEAL_TEST_PRIVATE_KEY and PROJECTSEAL_TEST_PUBLIC_KEY. Supply the key
password via Cosign's supported credential mechanism. This creates public log
records for synthetic content. Never use production keys for test fixtures.

```sh
pytest tests/integration/test_real_cosign.py::test_live_key_sign_and_verify -v
```

For keyless signing set PROJECTSEAL_KEYLESS_TEST=1, PROJECTSEAL_TEST_IDENTITY and
PROJECTSEAL_TEST_ISSUER, then run the keyless test with valid ambient OIDC credentials:

```sh
pytest tests/integration/test_real_cosign.py::test_live_keyless_sign_and_verify -v
```

The repository includes `cosign-live.yml`, manually dispatched on the reviewed
default branch only. Configure a protected `signing-integration` environment first.
It uses GitHub Actions OIDC and exact workflow identity, and exercises fresh
keyless artifact/manifest signing plus identity and tamper failures. It has not
been executed on GitHub here. For interactive local login use `projectseal sign`
and independently verify using your actual identity/issuer.

## External release prerequisites

1. Run the nine Python/platform CI combinations on GitHub; no remote CI result is
   available from this workspace. Run the opt-in keyless workflow or local login test.
2. Review current upstream advisories and the narrow Cosign pin, dependencies and
   pinned GitHub Actions. Upgrade and retest when necessary.
3. Configure a real repository/homepage, private vulnerability reporting and a
   maintainer conduct/security contact. No nonexistent addresses are advertised.
4. Reserve/confirm the PyPI name and configure Trusted Publishing for this exact
   repository, release workflow and `pypi` environment. Set environment reviewers,
   prevent self-review and restrict deployments to protected `v*` tags.
5. Review tag/source/version and build contents before approval. Tag pushes only
   test/build; publication requires manual dispatch with publish=true on the tag,
   followed by protected-environment approval. PR workflows never publish.

Publishing jobs only download built distributions and invoke the pinned PyPA
publisher with attestations; they never checkout, install or execute project
code. The workflow cannot enforce GitHub environment settings from YAML alone.

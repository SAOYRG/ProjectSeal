# Validation and release readiness

Validation date: **2026-10-24 (Asia/Shanghai)**. Repository:
[SAOYRG/ProjectSeal](https://github.com/SAOYRG/ProjectSeal). GitHub CI and keyless
signing checks are recorded below. The signed release workflow publishes to
[GitHub Releases](https://github.com/SAOYRG/ProjectSeal/releases); PyPI ownership
and Trusted Publishing binding still require the account setup in
[publishing](publishing.md).

## Actual GitHub results

- [Nine-platform CI passed](https://github.com/SAOYRG/ProjectSeal/actions/runs/40008733386):
  Ubuntu, Windows and macOS, each with Python 3.11, 3.12 and 3.13. Every job ran
  Ruff, formatting, mypy, pytest/coverage, wheel/sdist build, metadata checks and
  installed-wheel smoke checks.
- [Real GitHub Actions OIDC signing passed](https://github.com/SAOYRG/ProjectSeal/actions/runs/40009278448)
  with Cosign 3.1.4. Synthetic artifact and canonical manifest signatures verified;
  wrong identity and tampered content were rejected. Expected identity:
  `https://github.com/SAOYRG/ProjectSeal/.github/workflows/cosign-live.yml@refs/heads/main`;
  issuer: `https://token.actions.githubusercontent.com`.
- The `signing-integration` environment permits only `main`. Active ruleset
  `Maintainer-controlled release tags` restricts `v*` tag creation/update/deletion
  to SAOYRG. Private vulnerability reporting is enabled.
- The `pypi` environment permits only `v*` tags, requires SAOYRG's review and
  prohibits self-review. With the current single maintainer, a second authorized
  maintainer must participate in triggering/reviewing an actual publication.
  PyPI ownership and Trusted Publishing have not been configured or exercised.
- An initial live run failed during installation because the old installer used
  removed detached-signature assets. Updating the official pinned installer to
  v4.1.2 fixed that issue; the successful run above covers the corrected workflow.
- Upstream advisory review replaced the pre-release Cosign 3.0.2 pin with patched
  3.1.4 before source upload. Legacy and malformed bundles are explicitly rejected.

## Actual local results

- Windows amd64, Python 3.13.12: **117 passed, 3 skipped**, **96%** combined
  statement/branch coverage. The three skipped tests require external fixture/key/
  OIDC configuration. Hard-link protection also passed outside the restrictive sandbox.
- Ruff lint/format and strict mypy: passed.
- Real Cosign **3.1.4** official executable: GitHub asset SHA-256 matched
  `cbe953787074611f1334cbf37dc1cf953995bb8c45398eb4fc7bb781d29c1f2a`.
- Ordinary suite plus the configured real public fixture: **107 passed, 2 skipped**.
- Real public-release verification test: **1 passed**, including positive
  verification, modified bytes, incorrect exact signer identity and incorrect issuer.
  Fixture: official Cosign Windows executable and its public release bundle;
  expected identity `keyless@projectsigstore.iam.gserviceaccount.com`, issuer
  `https://accounts.google.com`, taken from Sigstore's installation documentation.
- Real key-based signing test: **1 passed**. Disposable Cosign-generated keys
  signed synthetic text plus its canonical manifest using default public services.
  Both signatures verified; modified content failed artifact verification and
  produced FILE_MODIFIED against the authenticated manifest. Disposable keys deleted.
- New `keygen` generated disposable encrypted keys through ProjectSeal, then the
  real key-based artifact/manifest and tamper checks passed again. Ordinary tests
  cover output collisions, failed generation cleanup, partial publication rollback,
  password requirements and private-output redaction. Persistent user keys were
  not generated or uploaded by the release process.
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

Put verified Cosign 3.1.4 on PATH and set these environment variables to an
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
Alternatively set `PROJECTSEAL_KEYGEN_TEST=1` to generate disposable keys with a
random password through ProjectSeal itself; remove the temporary keys afterward.

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
keyless artifact/manifest signing plus identity and tamper failures. Its successful
GitHub run is linked above. For interactive local login use `projectseal sign`
and independently verify using your actual identity/issuer.

## External release prerequisites

1. Recheck CI on the exact release commit. The nine-platform and real keyless
   checks above passed; a user's interactive local browser login was not tested.
2. Review current upstream advisories and the narrow Cosign pin, dependencies and
   pinned GitHub Actions. Upgrade and retest when necessary.
3. Keep the configured repository/homepage and private vulnerability reporting
   operational. No nonexistent contact addresses are advertised.
4. Reserve/confirm the PyPI name and configure Trusted Publishing for this exact
   repository, release workflow and `pypi` environment. The environment already
   has tag restrictions, required review and self-review prevention; add a second
   authorized maintainer before attempting a publication.
5. Review tag/source/version and build contents before tagging. Tag pushes run
   checks, build, sign, verify and publish a GitHub Release. PyPI publication
   requires manual dispatch with publish=true on the tag, followed by protected
   environment approval. PR workflows never publish.

Publishing jobs only download built distributions and invoke the pinned PyPA
publisher with attestations; they never checkout, install or execute project
code. The workflow cannot enforce GitHub environment settings from YAML alone.

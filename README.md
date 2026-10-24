# ProjectSeal CLI

<!-- Logo placeholder: a permanent project logo has not been selected. -->

**Verifiable software releases, with explicit signer trust.**

[简体中文](README.zh-CN.md) · [Quick start](docs/getting-started.md) ·
[CLI reference](docs/cli-reference.md) · [Security model](docs/security-model.md)

ProjectSeal is a local-first Python CLI for project identity records, SHA-256
fingerprints, Sigstore Cosign signing and identity-constrained verification.
No ProjectSeal account, database or server is required. Version **0.1.0** is an
initial release; see [validation status](docs/validation.md) and [publishing](docs/publishing.md).

## Features

- Initialize a versioned project UUID and self-declared metadata.
- Hash binary files in bounded 1 MiB chunks.
- Sign artifacts with modern Sigstore bundles; keyless signing is the default.
- Generate encrypted custom local keys with `keygen --output-prefix`.
- Require an exact signer identity and issuer, an explicitly supplied trust policy,
  or an independently trusted local public key when verifying.
- Optionally create **and separately sign** a canonical release manifest.
- Read Git branch, commit and dirty state; non-Git projects work too.
- Machine-readable JSON, explicit errors, overwrite protection and no telemetry.

## Security boundaries

A signature binds content to an expected identity or trusted key. A hash alone
does not identify an author. Project names, display names, UUIDs and Git history
are self-declared or contextual information. Neither a signature nor a signed
manifest establishes legal ownership, originality, safety, or copy protection.

**Local-first does not mean offline keyless signing.** Cosign uses OIDC, Fulcio,
Rekor and trusted-root services. Public transparency logs can expose signer
identity, artifact digest and signing metadata. ProjectSeal does not upload source
code or collect telemetry. See [privacy and trust](docs/security-model.md).

## Installation

Python **3.11+** is required. Install the published package from
[PyPI](https://pypi.org/project/projectseal/0.1.0/):

```sh
python -m pip install projectseal==0.1.0
projectseal --version
```

To install from this repository:

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install .
projectseal --help
projectseal --version
```

Download the wheel and signature from [GitHub Releases](https://github.com/SAOYRG/ProjectSeal/releases).
Verify it using [the signing guide](docs/signing-guide.md), then install with
`python -m pip install projectseal-0.1.0-py3-none-any.whl`.
PyPI publication is tracked separately in [publishing](docs/publishing.md).

### Cosign

This version accepts **Cosign 3.1.4 only** and probes its required flags. Download
the appropriate executable from the [official release](https://github.com/sigstore/cosign/releases/tag/v3.1.4),
verify it following the [official installation guide](https://docs.sigstore.dev/cosign/system_config/installation/),
and add it to `PATH` as `cosign` (`cosign.exe` on Windows). Choose Windows amd64,
macOS amd64/arm64, or Linux amd64/arm64 as appropriate. Do not silently substitute
an untested newer release. [Compatibility and test scope](docs/signing-guide.md).

## Quick start

```sh
projectseal init
projectseal status
projectseal identity --json
projectseal hash dist/app.zip --json
projectseal sign dist/app.zip
```

Cosign opens its authentication flow. Distribute both the artifact and
`dist/app.zip.sigstore.json`. Obtain the publisher's **expected exact identity
and issuer through an independent trusted channel**, then verify:

```sh
projectseal verify dist/app.zip --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

Replace the example identity and issuer with your actual trust constraints.
Verification without trust returns `UNTRUSTED` (or `MISSING_BUNDLE` if evidence
is absent) and exits nonzero. To authenticate project/version declarations:

```sh
projectseal sign dist/app.zip --release-version 0.1.0
projectseal verify dist/app.zip --manifest dist/app.zip.manifest.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

This produces the artifact bundle, canonical manifest and separate manifest
bundle. Plain artifact verification makes no claim about a nearby manifest.

## FAQ

**Is the developer name verified?** No. It is a local display field.

**Does this prevent copying, reverse engineering, or malicious releases?** No.
It verifies content and a supplied trust constraint, not software quality or rights.

**Why does verification say `VERIFICATION_FAILED` instead of identifying the cause?**
Cosign's exit code does not reliably distinguish identity, issuer, content,
signature and service errors. ProjectSeal avoids guessing. An authenticated
manifest allows a reliable `FILE_MODIFIED` digest comparison.

**Can I use CI or my own keys?** Yes. `init --non-interactive` never prompts;
`sign --non-interactive` accepts transparency-log consent and expects ambient
OIDC credentials or an accessible key. `--json` implies non-interactive signing.
Keep private keys outside the repository. See [the signing guide](docs/signing-guide.md).

**Must verification run in an initialized project?** No. Only manifest generation
requires initialization. Trust policies are only read via explicit `--policy`.

## Development

```sh
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest --cov=projectseal --cov-report=term-missing
python -m build
python -m twine check dist/*.whl dist/*.tar.gz
```

Ordinary tests mock external signing services. Live tests require explicit opt-in;
their environment is documented in [validation](docs/validation.md).
The Python 3.11/3.12/3.13 matrix on Ubuntu, Windows and macOS has passed on GitHub,
as has the real GitHub Actions OIDC signing test. See the linked validation record
for exact commits, workflow runs and remaining release prerequisites.

## Roadmap

- v0.2.0: Codex Skill, reusable release integration, broader tested Cosign versions.
- v0.3.0: development evidence records and optional licensing SDK.
- Later: optional Cloud, License and Shield integrations through explicit adapters.
  No cloud infrastructure is included in v0.1.0.

## Contributing and license

See [CONTRIBUTING](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md) and
[SECURITY](SECURITY.md). Licensed under [MIT](LICENSE). No third-party security
audit, adoption statistics or production assurance is claimed.

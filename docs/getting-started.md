# Getting started

Install Python 3.11+ and verified Cosign 3.0.2, then `python -m pip install .`
from this repository, preferably in a virtual environment.

```sh
projectseal init --name "My Application" --author "Developer" --website https://example.com --non-interactive
projectseal identity --json
projectseal status
projectseal hash dist/app.zip --json
projectseal sign dist/app.zip
projectseal verify dist/app.zip --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com --json
```

Build `dist/app.zip` using your normal release build first. Use your actual,
independently trusted identity/issuer. The current directory is the project root;
parent directories are not searched. Initialization refuses to overwrite an
existing UUID. Back up `.projectseal/project.json` before editing it.

Distribute the artifact and `FILE.sigstore.json`. Recipients establish their own
trust constraints. `VALID` means exit 0; unsuccessful verification exits nonzero.

To authenticate project/version declarations too:

```sh
projectseal sign dist/app.zip --release-version 0.1.0
projectseal verify dist/app.zip --manifest dist/app.zip.manifest.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

Signing again refuses existing outputs unless `--force` is supplied. Distribute
the artifact and all three sidecars. The manifest's signature is verified before
its digest and size are used. The artifact bundle is also verified. Only this
flow reports `manifest_authenticated: true`.

For CI, supply ambient OIDC credentials and `--non-interactive`. Signing `--json`
also implies non-interactive mode. See [the signing guide](signing-guide.md).

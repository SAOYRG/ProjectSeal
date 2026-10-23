# Signing guide

## Compatibility

The adapter pins **Cosign 3.0.2 exactly** and checks `version`, `sign-blob --help`
and `verify-blob --help`. Prereleases and other patch versions are rejected until
tested. This is an intentionally narrow tested interface, not a claim that this
release is the newest or suitable forever. Review upstream advisories before
publishing and expand the pin only after running the live suite.

Parameter references are the [pinned signing command](https://github.com/sigstore/cosign/blob/v3.0.2/doc/cosign_sign-blob.md),
[pinned verification command](https://github.com/sigstore/cosign/blob/v3.0.2/doc/cosign_verify-blob.md)
and [Sigstore quickstart](https://docs.sigstore.dev/quickstart/quickstart-cosign/).
The modern bundle format is the v3 default. No insecure skip flags are used.

## Keyless default

```sh
projectseal sign dist/app.zip --output dist/custom.sigstore.json
projectseal verify dist/app.zip --bundle dist/custom.sigstore.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

Cosign handles OIDC authentication, short-lived certificates, transparency evidence
and trust roots. Determine the correct exact SAN identity and issuer from your
provider and confirm them independently. ProjectSeal never derives trusted values
from downloaded certificates. A manifest requires a second sign-blob operation;
the provider may request authentication twice.

Ctrl+C cancels signing; staged outputs are removed and existing sidecars remain.
Other nonzero exits are signing failures, including user denial not distinguishable
from a general failure. ProjectSeal does not claim successful authentication from
a prompt or bundle inspection. Verify the final bundle against expected trust.

## CI and privacy

Use ambient credentials supported by Cosign (e.g. GitHub Actions OIDC), and
`--non-interactive`. This explicitly accepts transparency-log confirmation.
`--json` implies the same consent/non-interactive behavior. Without usable
credentials, signing fails or times out instead of waiting on terminal input.
Non-interactive keyless signing selects Cosign's `--fulcio-auth-flow token`
and closes stdin, preventing browser/device login fallback.
Signing timeout is 600 seconds; verification timeout 180 seconds.

No artifact bytes are deliberately uploaded by ProjectSeal. Cosign contacts public
services and logs signing metadata/digests. Public log entries may disclose your
identity. Git repository URLs have userinfo, query and fragment stripped before
automatic persistence. Do not put confidential data in project/manifest fields.

## Local keys

Generate and store your keys outside the repository using Cosign's own tooling.
Never commit private keys; the example names below point outside the project.

```sh
projectseal sign dist/app.zip --key /secure/location/cosign.key --non-interactive
projectseal verify dist/app.zip --key /trusted/location/cosign.pub
```

Supply passwords through Cosign's supported credential mechanism (for CI,
`COSIGN_PASSWORD` from a secret store), never command arguments or source files.
ProjectSeal does not generate, persist, print or manage private keys/passwords.
Key mode still retains Cosign's transparency/timestamp defaults. No offline-only
or log-skipping mode is provided. Public key possession alone does not establish
who owns that key: recipients must pre-establish trust themselves.

## Output safety

Existing outputs require `--force`. Input aliases, hard links and symlink output
files are rejected. Signing works on a temporary artifact snapshot and compares
the original afterward. It requires enough temporary disk space for the artifact;
hashing itself is streamed. Each sidecar publication is atomic. Ordinary I/O
errors roll back already-published sidecars, but a process/power failure between
multiple publications is not a transaction. Verify all files before distribution.

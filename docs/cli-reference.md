# CLI reference

`projectseal --version` prints the version. Each command supports `--help`,
`--json`, `--no-color`. Rich also respects `NO_COLOR`. Runtime JSON contains
exactly one JSON result, including errors. Typer syntax errors use stderr and
exit 2; they are not runtime JSON results.

| Command | Additional arguments/options | Behavior |
| --- | --- | --- |
| `init` | `--name`, `--author`, `--website`, `--non-interactive` | Create current-directory identity; JSON never prompts. |
| `identity` | none | Self-declared metadata; `authenticated: false`. |
| `status` | none | Config, Git and untrusted nearby release references. |
| `hash FILE` | none | `{file, algorithm, digest, size}`. |
| `sign FILE` | `--output/-o`, `--release-version`, `--key`, `--non-interactive`, `--force` | Default bundle `FILE.sigstore.json`; optional signed manifest. |
| `verify FILE` | `--bundle`, identity flags, `--policy`, `--key`, `--manifest`, `--manifest-bundle` | Require exactly one trust source. |

`status` discovers `*.manifest.json` in the current directory, `dist/` and
`releases/`. It never authenticates those references or scans dependencies.
`sign` returns custom output paths; verify those paths explicitly.

## Trust inputs

Use both `--certificate-identity` and `--certificate-oidc-issuer` with exact
values, or an explicitly trusted `--policy PATH`:

```json
{"schema_version":"1.0","certificate_identity":"dev@example.com","certificate_oidc_issuer":"https://accounts.google.com"}
```

Alternatively use `--key /trusted/location/cosign.pub`. Never trust a key or
policy just because it accompanies a download. Policies are not auto-loaded
from the project, manifest or bundle. Identity, policy and key modes conflict.
No regex, remote key, KMS URI, identity-token argument or insecure bypass option
is exposed. `sign --key` uses a local private key; `verify --key` a local public key.

## Verification status

| Status | Meaning |
| --- | --- |
| `VALID` | Cosign exited 0 with signature, integrity and explicit trust checks. |
| `FILE_MODIFIED` | Authenticated manifest digest/size differs, or concurrent content change. |
| `MISSING_BUNDLE` | Artifact or requested manifest evidence missing. |
| `UNTRUSTED` | No complete independent trust constraint. |
| `TOOL_ERROR` | Missing/incompatible tool, startup failure or timeout. |
| `VERIFICATION_FAILED` | Cosign nonzero; exact cause cannot reliably be distinguished. |
| `INVALID_MANIFEST` | Authenticated manifest violates schema or canonical byte rules. |

The API reserves `INVALID_SIGNATURE` and `IDENTITY_MISMATCH` for a backend with
reliable structured evidence. This Cosign adapter does not infer them from error
strings. Wrong identity, issuer, bundle corruption and artifact-only tampering
normally yield `VERIFICATION_FAILED`.

Exit codes: 0 success, 1 runtime/verification failure, 2 syntax error, 130 explicit
cancellation. Interactive Cosign stderr is inherited for authentication/consent;
stdout is captured. JSON/CI captures diagnostics without echoing secrets.

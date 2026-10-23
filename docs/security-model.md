# Security model

## What is established

With an independently trusted identity and OIDC issuer, or public key, Cosign
verifies the artifact signature, integrity and applicable certificate, timestamp
and transparency evidence. ProjectSeal does not reimplement cryptography.
Authenticated release manifests bind a signed project/version declaration to the
artifact's SHA-256/size, creating a verifiable origin record.

## What is not established

This does not prevent copying, reverse engineering or redistribution; establish
copyright ownership or originality; stop an authorized signer signing malicious
code; or guarantee that a signed release is safe, vulnerability-free or audited.
Local UUID/name/author fields do not authenticate a person. Git dates are not
trusted legal timestamps. Manifest timestamps are signer declarations, not
independent time evidence. Cosign validates its own signed timestamp/log evidence.

## Trust boundaries and adversaries

A network attacker replacing an artifact or bundle must still satisfy Cosign and
the recipient's independent trust constraint. An attacker changing an unsigned
manifest cannot gain authenticated claims: verification requires its separate
bundle before using any digest. An attacker replacing a downloaded policy/key
can defeat verification if the recipient blindly trusts that replacement.
No trust source is auto-loaded from a repository or sidecar.

The Python runtime, dependencies, OS, selected PATH executables, system time,
Cosign trusted-root configuration and the supplied trust inputs must be trusted.
Malware running as the same user, stolen keys, compromised identity providers,
malicious Cosign binaries and malicious configured trust roots are outside this
tool's protection. Cosign environment settings can change service/root behavior;
review CI environment and do not run untrusted code in privileged signing jobs.

Inputs are validated; subprocesses use argument lists and shell=False. External
diagnostics are not placed in captured JSON, exception messages or application
logs. Interactive Cosign stderr is shown directly for login/consent and is not
redacted by ProjectSeal; never enable shell tracing around credentials.

## Files and races

Files are copied to temporary working snapshots; original content is checked
afterward. This consumes disk space proportional to artifact size. It protects
against ordinary concurrent edits, not an adversarial same-user filesystem.
Each sidecar is atomically published, with no-clobber by default. Force is
explicit. Multi-file crash consistency is not guaranteed; distribute only a
complete, verified set. Temporary files are cleaned on normal failure/cancellation;
abrupt OS termination may leave temporary data, subject to local permissions.

## Privacy and external services

ProjectSeal has no telemetry, user account system or backend. Local init/hash/
identity/status require no network (optional Git queries are local). Keyless
signing contacts Sigstore and an OIDC provider. Verification may fetch trusted
roots/evidence. Public logs can disclose signer identity, artifact digests and
signing metadata; entries may be permanent. Source file bytes are not intentionally
uploaded by ProjectSeal. Consult the providers' terms before signing confidential
material. An authenticated manifest's contents become public when you distribute it.

## Failure honesty

Only Cosign exit 0 with explicit trust can yield VALID. A nonzero verification
exit is generally VERIFICATION_FAILED; stderr is not treated as a structured API.
FILE_MODIFIED is emitted only for an authenticated manifest mismatch or detected
concurrent change. No accepted signer/manifest claims are returned on failure.
No mock/stub result is evidence of real cryptographic interoperability.

See [SECURITY](../SECURITY.md) for reporting and supported versions.

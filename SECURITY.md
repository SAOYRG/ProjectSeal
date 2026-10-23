# Security policy

## Supported versions

Only the latest 0.1.x patch will receive fixes while 0.1.x is maintained. This
initial 0.1.0 release candidate has no third-party security audit. Its Cosign
compatibility pin is not a guarantee of perpetual upstream security support.
Review current Sigstore advisories before release/deployment.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/SAOYRG/ProjectSeal/security/advisories/new).
Private reporting is enabled for this repository. If GitHub reporting is
temporarily unavailable, open an issue asking for a private contact channel
**without exploit details, credentials or sensitive artifacts**. No fictional
security mailbox or response-time SLA is advertised.

Include the version, operating system, expected trust constraint, minimal
reproduction and impact. Redact tokens, passwords and private keys. Do not attach
confidential software. We will coordinate reproduction, remediation and disclosure.

See [the security model](docs/security-model.md) for trust assumptions, external
service privacy and limits. Signatures are not copyright or software-safety proof.

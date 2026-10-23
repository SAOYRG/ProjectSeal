# Architecture

`commands/` owns argument parsing and presentation. `core/` owns local identity,
Git metadata, streaming hashing, canonical manifests, signing orchestration and
verification policy enforcement. `signing/base.py` defines a `SigningBackend`
protocol; `signing/cosign.py` supplies the pinned external-tool implementation.
`utils/` isolates atomic publication, strict JSON, output and subprocess execution.
Core APIs accept `Path` objects and return Pydantic models or plain records; they
are callable independently of Typer, including dependency-injected test backends.

## Records

Project identity: `.projectseal/project.json`, schema `1.0`, UUID, name, author
display name/homepage, optional repository and timezone-aware UTC creation time.
The metadata is self-declared and ignored by trust decisions.

Artifact evidence: `FILE.sigstore.json`, a native modern Cosign bundle covering
the original artifact bytes. Without `--release-version`, no project is needed.

Release manifest: `FILE.manifest.json` plus its own `.sigstore.json`, produced
with `sign --release-version VERSION`. Fields: schema_version, project_id,
project_name, version, artifact (filename/size/sha256), source (git_commit and
repository), and UTC created_at. Fields are validated; extra fields are rejected.

## Canonical manifest serialization, version 1.0

Validate the schema; dump JSON-mode values with all declared fields present,
including explicit nulls. Encode UTF-8 without BOM, lexicographically sort object
keys, use `,` and `:` separators without whitespace, keep Unicode unescaped,
disallow NaN/Infinity, and append **no newline**. Datetimes use Pydantic JSON-mode
UTC RFC3339 form (`Z`, optional microseconds). No floating-point fields occur.
Unicode is preserved without normalization. This is a ProjectSeal-specific rule,
not an implementation of RFC 8785. Future encodings require a new schema version.

Sign the resulting exact bytes as a blob. Verification authenticates those bytes
first, validates schema and requires byte-for-byte canonical reserialization.
Only then use its SHA-256/size to bind to the artifact. The separate artifact
signature is checked with the same explicitly supplied trust constraint. A file
may be renamed; filename is a signed declaration, not a path to open or execute.

## Trust and failure handling

Trust enters through exact CLI identity/issuer, explicit policy file, or local
trusted public key. It is never inferred from project, manifest, bundle or Git.
Temporary snapshots reduce ordinary concurrent modification risks; post-checks
detect changed content. Same-user malware, malicious executables or compromised
OS trust are outside this boundary. Process arguments are arrays with shell=False;
captured tool diagnostics never become user-visible exceptions.

## Future extension seams

Cloud may consume explicit release records through an optional `ReleaseStore`
adapter (put/get/list) with opt-in network transport. A future License service may
provide a separate issuance/revocation protocol and SDK; it must not reuse project
display names as authenticated owners. Shield integrations may implement build
inspection adapters before signing, with separate findings/provenance. None of
these interfaces is implemented or required in v0.1.0. No database, Redis, login,
payments or cloud SDK dependency is introduced.

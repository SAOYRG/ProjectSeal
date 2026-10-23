# Python demo

Install ProjectSeal from the repository root, then run the following in this folder:

```sh
python make_release.py
projectseal init --name PythonDemo --author Developer --non-interactive
projectseal hash dist/app.zip --json
projectseal sign dist/app.zip --release-version 0.1.0
projectseal verify dist/app.zip --manifest dist/app.zip.manifest.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

The last command needs your real, independently trusted identity/issuer. Signing
requires verified Cosign 3.0.2 and OIDC login. The demo has no bundled keys/tokens.

# Release and Trusted Publishing

Repository: [SAOYRG/ProjectSeal](https://github.com/SAOYRG/ProjectSeal).
GitHub Releases and PyPI are separate publication destinations.

## Published v0.1.0

Published to [PyPI](https://pypi.org/project/projectseal/0.1.0/) on
2026-10-24 at 12:15 (Asia/Shanghai), following explicit human approval of
[this release run](https://github.com/SAOYRG/ProjectSeal/actions/runs/40059992756).
All nine CI jobs, build and Trusted Publishing with Sigstore attestations passed.
The package files are byte-for-byte identical to the signed
[GitHub Release](https://github.com/SAOYRG/ProjectSeal/releases/tag/v0.1.0).
The immutable release tag resolves to `2c88f7f3829e12eb75166221ad34c988f7d265e3`.

| File | SHA-256 |
| --- | --- |
| `projectseal-0.1.0-py3-none-any.whl` | `836c981e80d238b7e2a3f6ec35d20129b0bc496eb57ca9d07157a53327db5405` |
| `projectseal-0.1.0.tar.gz` | `d7e8ca3dd46d99679ef4094df752fc344507c11bab6ec29288dab2b41aecb39d` |

PyPI's Integrity API reports repository `SAOYRG/ProjectSeal`, workflow
`release.yml`, environment `pypi` for both files. Independently verified both
public attestations using `pypi-attestations 0.0.30` with explicit expected
repository `https://github.com/SAOYRG/ProjectSeal`; both returned `OK`.
Installation from the public PyPI index passed version, keygen help and dependency
checks in a separate environment. No long-lived PyPI API token was used.

```sh
python -m pip install projectseal==0.1.0
pypi-attestations verify pypi --repository https://github.com/SAOYRG/ProjectSeal pypi:projectseal-0.1.0-py3-none-any.whl
pypi-attestations verify pypi --repository https://github.com/SAOYRG/ProjectSeal pypi:projectseal-0.1.0.tar.gz
```

Install `pypi-attestations` separately when reproducing the optional provenance
checks; it is not a ProjectSeal runtime dependency. Cosign 3.1.4 is still required
for ProjectSeal's own sign/verify/keygen commands.

## GitHub Release

The maintainer creates a protected `v*` tag matching `pyproject.toml`. The
`release.yml` workflow runs all nine OS/Python checks, builds and checks wheel
and sdist, signs both distributions and `SHA256SUMS` using Cosign 3.1.4 and GitHub
OIDC, verifies their exact workflow identity, then uploads all six files to a
GitHub Release. The signing job executes no project code. The upload job has
contents-write access, with no OIDC token and no source checkout.

Tag pushes publish to GitHub only. They never upload to PyPI. A failed GitHub
publication may be retried via workflow_dispatch on the same tag with
`github_release=true` and `publish=false`; existing releases are not overwritten.
See [signature verification](signing-guide.md#verify-projectseals-own-github-release).

## First PyPI binding

The first publication used a pending publisher registered by the owner after
email verification and 2FA setup. For a new project, a PyPI account can register
a pending publisher at
[account publishing](https://pypi.org/manage/account/publishing/):

| PyPI field | Exact value |
| --- | --- |
| PyPI Project Name | `projectseal` |
| GitHub repository owner | `SAOYRG` |
| GitHub repository name | `ProjectSeal` |
| Workflow name | `release.yml` (filename only) |
| Environment name | `pypi` |

For a project that already exists under your account, add the same publisher in
that project's Publishing settings instead. This now applies to `projectseal`;
the first publication completed the pending-publisher setup. Follow the official
[pending-publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
or [existing-project guide](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
Pending publisher registration does not itself publish or reserve a project name.

The GitHub half is configured: `id-token: write`, PyPA's publisher with
attestations, and environment `pypi` limited to `v*` tags. SAOYRG review is
required. On 2026-10-24 the owner explicitly authorized SAOYRG to review releases
that SAOYRG triggered, so `prevent_self_review` is false. Human approval is still
required for every publication; the reviewer and tag restrictions remain active.
This permits a single-maintainer release without an independent second reviewer.

After the PyPI binding and reviewers are ready, dispatch `release.yml` on
`v0.1.0` with `publish=true` and `github_release=false`. Approve the protected
environment using an eligible account. The privileged publisher only downloads
the checked distributions and invokes the pinned official PyPA action.

No PyPI token/password belongs in GitHub Secrets or this chat for this workflow.
A custom Cosign private key is unrelated to PyPI OIDC authentication.
Successful publication must be confirmed on PyPI and its provenance page;
workflow configuration alone is not evidence of a completed binding or upload.

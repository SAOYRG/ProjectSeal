# Release and Trusted Publishing

Repository: [SAOYRG/ProjectSeal](https://github.com/SAOYRG/ProjectSeal).
GitHub Releases and PyPI are separate publication destinations.

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

At the last check, `https://pypi.org/pypi/projectseal/json` returned 404. This
does not reserve the name or guarantee that PyPI will accept it. A PyPI account
with verified email and configured 2FA must register a pending publisher at
[account publishing](https://pypi.org/manage/account/publishing/):

| PyPI field | Exact value |
| --- | --- |
| PyPI Project Name | `projectseal` |
| GitHub repository owner | `SAOYRG` |
| GitHub repository name | `ProjectSeal` |
| Workflow name | `release.yml` (filename only) |
| Environment name | `pypi` |

For a project that already exists under your account, add the same publisher in
that project's Publishing settings instead. Follow the official
[pending-publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
or [existing-project guide](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
Pending publisher registration does not itself publish or reserve a project name.

The GitHub half is configured: `id-token: write`, PyPA's publisher with
attestations, and environment `pypi` limited to `v*` tags. SAOYRG review is
required and self-review is prohibited. A second authorized maintainer must
participate in triggering/reviewing publication. Do not remove this gate to
work around an approval failure.

After the PyPI binding and reviewers are ready, dispatch `release.yml` on
`v0.1.0` with `publish=true` and `github_release=false`. Approve the protected
environment using an eligible account. The privileged publisher only downloads
the checked distributions and invokes the pinned official PyPA action.

No PyPI token/password belongs in GitHub Secrets or this chat for this workflow.
A custom Cosign private key is unrelated to PyPI OIDC authentication.
Successful publication must be confirmed on PyPI and its provenance page;
workflow configuration alone is not evidence of a completed binding or upload.

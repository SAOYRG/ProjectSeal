# Contributing

Use Python 3.11+ and a virtual environment, then `python -m pip install -e
".[dev]"`. Keep business logic in core modules and external tool integration in
the signing adapter. Add tests for changed behavior and critical failure paths.

Before submitting:

```sh
ruff check .
ruff format --check .
mypy src
pytest --cov=projectseal --cov-report=term-missing
python -m build
python -m twine check dist/*.whl dist/*.tar.gz
```

Never commit real private keys, credentials or confidential artifacts. Ordinary
tests must not depend on live authentication. Mark real Cosign tests explicitly
and document exactly what ran; mocks do not demonstrate cryptographic correctness.
Changes to trust, subprocess flags or canonical serialization require focused
security tests and documentation. See [validation](docs/validation.md).

PRs should explain the concrete problem, resulting behavior, validation and limits.
Follow [the Code of Conduct](CODE_OF_CONDUCT.md) and report sensitive vulnerabilities
using [SECURITY](SECURITY.md). Contributions are under the MIT license.

## Release review

Before any public release, complete docs/validation.md's external checks, configure
GitHub private vulnerability reporting, reserve the package name, configure PyPI
Trusted Publishing, and protect the GitHub `pypi` environment with required
reviewers, prevent-self-review and tag-only deployment rules. Protect release tags.
The workflow cannot enforce environment protection by itself. Review both the tag
and workflow before approving. Public hosting/publishing requires maintainer action.

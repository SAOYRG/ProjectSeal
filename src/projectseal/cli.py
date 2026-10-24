import typer

from projectseal import __version__
from projectseal.commands import hash, identity, init, keygen, sign, status, verify

app = typer.Typer(
    name="projectseal",
    help="ProjectSeal: sign release artifacts and verify explicit signer trust.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def show_version(value: bool) -> None:
    if value:
        typer.echo(f"ProjectSeal {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=show_version, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """Local project identity, streaming SHA-256 and Sigstore Cosign signatures."""


app.command("init")(init.command)
app.command("identity")(identity.command)
app.command("status")(status.command)
app.command("hash")(hash.command)
app.command("keygen")(keygen.command)
app.command("sign")(sign.command)
app.command("verify")(verify.command)

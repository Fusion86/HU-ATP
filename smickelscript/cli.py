import os
import click


@click.group()
def cli():
    """SmickelScript command line interface."""
    pass


@cli.command()
@click.argument("args", required=False, nargs=-1)
@click.option("--input", "-i", type=str, help="Input source file", required=True)
@click.option("--entrypoint", "-e", type=str, help="Entrypoint (default is main)", default="main")
@click.option("--trace/--no-trace", type=bool, help="Show trace logging", default=False)
def exec(input, entrypoint: str, trace: bool, args):
    """Execute a SmickelScript file."""

    def parse_arg(x: str):
        if len(x) == 0:
            return ""
        try:
            return int(x)
        except Exception:
            return x

    if trace:
        os.environ["SMICKEL_TRACE"] = "1"

    # This needs to happen AFTER settings os.environ
    from smickelscript import interpreter

    # If you want to use map then I guess this works too.
    args = list(map(parse_arg, args))

    # Pythonic way to solve this.
    # args = [parse_arg(x) for x in args]

    print("> Executing {} function in '{}' with args {}".format(entrypoint, input, args))
    try:
        retval = interpreter.run_file(input, entrypoint, args)
        print("> Function returned: {}".format(retval))
    except Exception as ex:
        print("> {}".format(ex))


if __name__ == "__main__":
    cli()

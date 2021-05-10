import click
from smickelscript import interpreter


@click.group()
def cli():
    """Click group."""
    pass


@cli.command()
@click.argument("args", required=False, nargs=-1)
@click.option("--input", "-i", type=str, help="Input source file")
@click.option("--entrypoint", "-e", type=str, help="Entrypoint (default is main)", default="main")
def exec(input, entrypoint: str, args):
    def parse_arg(x: str):
        if len(x) == 0:
            return ""
        try:
            return int(x)
        except Exception:
            return x

    # If you want to use map then I guess this works too.
    # args = list(map(parse_arg, args.split(" ")))

    # Pythonic way to solve this.
    args = [parse_arg(x) for x in args]

    print("> Executing {} function in '{}' with args {}".format(entrypoint, input, args))
    retval = interpreter.run_file(input, entrypoint, args)
    print("> Function returned: {}".format(retval))


if __name__ == "__main__":
    cli()

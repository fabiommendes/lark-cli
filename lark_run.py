import sys
from functools import wraps
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, cast

import lark
import rich
import typer
from rich.console import Console
from rich.padding import Padding
from rich.tree import Tree

stderr = Console(file=sys.stderr)
stdout = Console()


def safe[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """
    A decorator that wraps a function and catches any exceptions so we don't
    dump tracebacks to the user.
    """

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            rich.print(f"[bold red]Error:[/] {e}", file=sys.stderr)
            exit(1)

    return wrapper


app = typer.Typer(
    name="Lark",
    help="A simple command-line interface for Lark, the parsing Library.",
    no_args_is_help=True,
)


@app.command()
@safe
def main(
    file: Annotated[
        Path,
        typer.Argument(
            ...,
            help="The path to the file to parse.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    test: Annotated[
        Path | None,
        typer.Option(
            ...,
            "-t",
            "--test",
            help="The path to the test file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            ...,
            "-v",
            "--verbose",
            help="Enable verbose output for tests.",
        ),
    ] = False,
    parser: Annotated[
        str | None,
        typer.Option(
            ...,
            "-p",
            "--parser",
            help="The parser to use. Can be one of 'earley', 'lalr', or 'cyk'.",
            case_sensitive=False,
            show_default=True,
        ),
    ] = None,
    command: Annotated[
        str | None,
        typer.Option(
            ...,
            "-c",
            "--command",
            help="The source code to parse. If not provided, the program will enter REPL mode.",
        ),
    ] = None,
    start: Annotated[
        str,
        typer.Option(
            ...,
            "-s",
            "--start",
            help="The start symbol for the grammar.",
        ),
    ] = "start",
) -> None:
    """
    Test Lark grammar against examples or interactively.
    """
    if parser not in ("earley", "lalr", "cyk", None):
        msg = f"[bold red]Error:[/] Invalid parser {parser}. Must be one of 'earley', 'lalr', 'cyk', or 'auto'."
        stderr.print(msg)
        exit(1)

    try:
        with file.open() as f:
            parser = cast(Literal["earley", "lalr", "cyk"], parser)
            grammar = lark.Lark(f.read(), parser=parser or "earley", start=start)
    except Exception as e:
        stderr.print("[bold red]Error:[/] invalid grammar")
        stderr.print(Padding(str(e), 2, style="red"))
        rich.print(e.args, type(e))
        exit(1)

    if test is not None:
        examples = read_examples(test)
        for line in examples[0]:
            try:
                stdout.print(f"[blue]{line}  ", end="")
                ast = grammar.parse(line)
                stdout.print("  [bold green]✓[/]")
                if verbose:
                    stdout.print(Padding(render_tree(ast), 2))
            except lark.LarkError as e:
                stdout.print("  [bold red]✗[/]")
                if verbose:
                    stdout.print(Padding(str(e), 2, style="red"))

        for line in examples[1]:
            try:
                stdout.print(f"[blue]{line}  ", end="")
                ast = grammar.parse(line)
                stdout.print("  [bold red]✗[/] (it should fail)")
                if verbose:
                    stdout.print(Padding(render_tree(ast), 2))
            except lark.LarkError:
                stdout.print("  [bold green]✓[/]")
    elif command is not None:
        try:
            ast = grammar.parse(command)
            stdout.print(render_tree(ast))
        except lark.LarkError as e:
            stderr.print(f"[bold red]Error:[/] {e}")
    else:
        repl(grammar)


def read_examples(path: Path) -> tuple[list[str], list[str]]:
    match path.suffix.lower():
        case ".txt" | ".examples" | ".test" | "":
            with path.open() as f:
                return list(f), []
        case ".json":
            import json

            with path.open() as f:
                return load_from_data(json.load(f))

        case ".yaml" | ".yml":
            import yaml

            with path.open() as f:
                return load_from_data(yaml.safe_load(f))
        case _:
            stderr.print(f"[bold red]Error:[/] unsupported file format {path.suffix}")
            exit(1)


def load_from_data(data: Any) -> tuple[list[str], list[str]]:
    if isinstance(data, list):
        if not all(isinstance(line, str) for line in data):
            stderr.print("[bold red]Error:[/] invalid data format")
            exit(1)
        return data, []
    elif isinstance(data, dict):
        accept = data.get("accept", [])
        reject = data.get("reject", [])
        if not isinstance(accept, list) or not isinstance(reject, list):
            stderr.print("[bold red]Error:[/] invalid data format")
            exit(1)
        return accept, reject
    else:
        stderr.print("[bold red]Error:[/] unsupported data format")
        exit(1)


def repl(grammar: lark.Lark) -> None:
    msg = "[bold green]Welcome to the Lark REPL[/] [dim](type 'exit' to quit)[/]"
    stdout.print(msg)

    while True:
        try:
            line = input("> ")
            if line.strip() == "exit":
                break
            ast = grammar.parse(line)
            stdout.print(render_tree(ast))
        except lark.LarkError as e:
            stderr.print(f"[bold red]Error:[/] {e}")


def render_tree(tree: lark.Tree) -> Tree:
    node = Tree(tree.data, style="blue bold", guide_style="cyan")

    for child in tree.children:
        if isinstance(child, lark.Tree):
            node.add(render_tree(child))
        elif isinstance(child, lark.Token):
            node.add(f"[green dim]{child.type}([yellow]{child.value}[/])[/]")
        else:
            node.add(repr(child))
    return node


if __name__ == "__main__":
    app()

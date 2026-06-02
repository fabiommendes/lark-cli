# Lark CLI

A simple command-line interface for Lark, the parsing Library.


## Installation

You can install Lark CLI using pip:

```bash
pip install lark-cli
```

Or let uv or pipx handle it for you:

```bash
uvx lark-cli YOUR_FILE.lark  # install automatically in the background
```

# Usage

To use Lark CLI, simply run the command followed by the path to your Lark
grammar file:

```bash
lark YOUR_FILE.lark
```

This will open a REPL where you can enter strings to be parsed according to the
grammar defined in `YOUR_FILE.lark`. The CLI will display the parse tree for
each input string.

You can also specify a test input file containing strings that should be
accepted or rejected by the grammar:

```bash
lark YOUR_FILE.lark -t TEST_INPUTS.yaml
```

It expects a YAML or JSON file with the following structure:

```yaml
accept:
  - "valid string 1"
  - "valid string 2"    
reject:
    - "invalid string 1"
    - "invalid string 2"
```
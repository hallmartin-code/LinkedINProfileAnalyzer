"""CLI entry point: deck (PDF/PPTX) -> structured data -> branded one-pager PDF."""

import json
import os
import sys

import click
from rich.console import Console
from rich.panel import Panel

from parser import parse_deck
from extractor import extract_structured_data
from generator import generate_onepager

console = Console()

# Default logo location; header renders without a logo if this is absent.
_DEFAULT_LOGO = os.path.join(os.path.dirname(__file__), "assets", "logo.png")


@click.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    help="Path to PDF or PPTX pitch deck.",
)
@click.option(
    "--output",
    "output_dir",
    default="output",
    show_default=True,
    help="Output directory for the generated one-pager PDF.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print the extracted JSON before generating the PDF.",
)
def cli(input_path, output_dir, debug):
    """Generate a one-pager PDF summary from an investor pitch deck."""
    # --- Validate input file ---
    if not os.path.exists(input_path):
        console.print(f"[bold red]Error:[/] Input file not found: {input_path}")
        sys.exit(1)

    try:
        # --- Parse ---
        with console.status("[cyan]Parsing deck...", spinner="dots"):
            slides = parse_deck(input_path)
        console.print(f"[green]Parsed[/] {len(slides)} slide(s) from deck.")

        # --- Extract (AI) ---
        with console.status("[cyan]Extracting structured data with Claude...", spinner="dots"):
            data = extract_structured_data(slides)
        console.print("[green]Extracted[/] structured company data.")

        if debug:
            console.print(
                Panel(
                    json.dumps(data, indent=2),
                    title="Extracted JSON",
                    border_style="magenta",
                )
            )

        # --- Generate PDF ---
        logo = _DEFAULT_LOGO if os.path.exists(_DEFAULT_LOGO) else None
        with console.status("[cyan]Generating one-pager PDF...", spinner="dots"):
            out_path = generate_onepager(data, output_dir=output_dir, logo_path=logo)

        console.print(
            Panel(
                f"[bold green]Success![/] One-pager saved to:\n[bold]{out_path}[/]",
                border_style="green",
            )
        )

    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)
    except ValueError as exc:
        # Unsupported format, etc.
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)
    except RuntimeError as exc:
        # Missing API key, PDF/parse failures with clean messages.
        console.print(f"[bold red]Error:[/] {exc}")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - last-resort catch-all
        console.print(f"[bold red]Unexpected error:[/] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    cli()

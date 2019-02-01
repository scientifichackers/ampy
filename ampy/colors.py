from textwrap import dedent

import click


def black(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="black", **opts)


def black_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="black", **opts)


def red(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="red", **opts)


def red_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="red", **opts)


def green(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="green", **opts)


def green_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="green", **opts)


def yellow(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="yellow", **opts)


def yellow_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="yellow", **opts)


def blue(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="blue", **opts)


def blue_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="blue", **opts)


def magenta(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="magenta", **opts)


def magenta_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="magenta", **opts)


def cyan(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="cyan", **opts)


def cyan_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="cyan", **opts)


def white(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="white", **opts)


def white_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="white", **opts)


def bright_black(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_black", **opts)


def bright_black_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_black", **opts)


def bright_red(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_red", **opts)


def bright_red_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_red", **opts)


def bright_green(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_green", **opts)


def bright_green_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_green", **opts)


def bright_yellow(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_yellow", **opts)


def bright_yellow_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_yellow", **opts)


def bright_blue(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_blue", **opts)


def bright_blue_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_blue", **opts)


def bright_magenta(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_magenta", **opts)


def bright_magenta_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_magenta", **opts)


def bright_cyan(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_cyan", **opts)


def bright_cyan_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_cyan", **opts)


def bright_white(*text: str, **opts) -> str:
    return click.style(" ".join(text), fg="bright_white", **opts)


def bright_white_bg(*text: str, **opts) -> str:
    return click.style(" ".join(text), bg="bright_white", **opts)


def bold(*text: str, **opts) -> str:
    return click.style(" ".join(text), bold=True)


COLOR_LIST = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
)


def _codegen():
    """generates python functions for various colors."""
    for color in COLOR_LIST:
        print(
            dedent(
                f"""
                def {color}(*text: str, **opts)->str:
                    return click.style(" ".join(text), fg="{color}", **opts)    
                """
            )
        )
        print(
            dedent(
                f"""
                def {color}_bg(*text: str, **opts) -> str:
                    return click.style(" ".join(text), bg="{color}", **opts)    
                """
            )
        )


if __name__ == '__main__':
    _codegen()

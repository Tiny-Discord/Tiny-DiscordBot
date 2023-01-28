import argparse


def parse_cli_flags() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        prog="TinyBot", description="TinyBot launcher", allow_abbrev=True
    )
    parser.add_argument("--prefix", type=str, default="!", help="The prefix used for the bot.")
    parser.add_argument(
        "--dotenvfile-path",
        type=str,
        default=None,
        help="The path where the .env file is located.",
    )
    return parser.parse_known_args()

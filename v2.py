#!/usr/bin/env python3

import argparse
import subprocess
import uuid
import time
import sys
from datetime import datetime

try:
    from colorama import init, Fore, Style

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""

    class Style:
        RESET_ALL = BRIGHT = DIM = ""


PUSH_INTERVAL = 50000


def get_colors(no_color=False):
    if no_color or not COLORS_AVAILABLE:

        class NoColorFore:
            RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""

        class NoColorStyle:
            RESET_ALL = BRIGHT = DIM = ""

        return NoColorFore(), NoColorStyle()

    return Fore, Style


def run_git_command(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )


def verify_git_repo():
    result = run_git_command(["git", "rev-parse", "--is-inside-work-tree"])

    if result.returncode != 0:
        print(f"{F.RED}✗ Not inside a git repository{S.RESET_ALL}")
        sys.exit(1)


def verify_git_identity():
    name = run_git_command(["git", "config", "user.name"])
    email = run_git_command(["git", "config", "user.email"])

    if not name.stdout.strip() or not email.stdout.strip():
        print(f"{F.RED}✗ Git identity is not configured{S.RESET_ALL}")
        print()
        print(f"{F.YELLOW}Run:{S.RESET_ALL}")
        print('git config --global user.name "yourname"')
        print('git config --global user.email "you@example.com"')
        sys.exit(1)


def push_commits(current_count, dry_run):
    print()

    if dry_run:
        print(
            f"{F.YELLOW}[DRY RUN]{S.RESET_ALL} "
            f"{F.WHITE}git push{S.RESET_ALL} "
            f"{F.CYAN}(after {current_count} commits){S.RESET_ALL}"
        )
        return

    print(
        f"{F.BLUE}Pushing after "
        f"{F.WHITE}{current_count}{S.RESET_ALL} "
        f"{F.BLUE}commits...{S.RESET_ALL}"
    )

    result = run_git_command(["git", "push"])

    if result.returncode != 0:
        print(f"{F.RED}✗ Push failed{S.RESET_ALL}")

        if result.stderr:
            print(result.stderr.strip())

        return

    print(f"{F.GREEN}✓ Push completed{S.RESET_ALL}")


def progress_line(i, total, start_time):
    elapsed = time.time() - start_time

    rate = i / elapsed if elapsed > 0 else 0

    eta = (total - i) / rate if rate > 0 else 0

    percent = (i / total) * 100

    width = 24
    filled = int(width * (i / total))

    bar = "█" * filled + "░" * (width - filled)

    return (
        f"\r"
        f"{F.CYAN}[{i:>{len(str(total))}}/{total}]{S.RESET_ALL} "
        f"{F.GREEN}[{bar}]{S.RESET_ALL} "
        f"{F.MAGENTA}{percent:>6.2f}%{S.RESET_ALL} "
        f"{F.WHITE}{rate:>7.2f}{S.RESET_ALL} "
        f"{F.GREEN}commits/s{S.RESET_ALL} "
        f"{F.BLUE}ETA:{S.RESET_ALL} "
        f"{F.WHITE}{eta:>7.1f}s{S.RESET_ALL}"
    )


parser = argparse.ArgumentParser(
    description="Mass git empty commit generator"
)

parser.add_argument(
    "count",
    type=int,
    help="Number of commits to create"
)

parser.add_argument(
    "-p",
    "--push",
    action="store_true",
    help="Push commits periodically"
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not execute git commands"
)

parser.add_argument(
    "--no-color",
    action="store_true",
    help="Disable colored output"
)

args = parser.parse_args()

F, S = get_colors(args.no_color)

if args.count <= 0:
    print(f"{F.RED}✗ Count must be greater than 0{S.RESET_ALL}")
    sys.exit(1)

if not args.dry_run:
    verify_git_repo()
    verify_git_identity()

print(
    f"{F.CYAN}Starting creation of "
    f"{F.WHITE}{args.count}{S.RESET_ALL} "
    f"{F.CYAN}commits{S.RESET_ALL}"
)

print(
    f"{F.YELLOW}Push interval:{S.RESET_ALL} "
    f"{F.WHITE}{PUSH_INTERVAL}{S.RESET_ALL}"
)

print(
    f"{F.GREEN}Started:{S.RESET_ALL} "
    f"{F.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{S.RESET_ALL}"
)

print(f"{F.BLUE}{'=' * 90}{S.RESET_ALL}")

start_time = time.time()

successful = 0
failed = 0

for i in range(1, args.count + 1):
    msg = str(uuid.uuid4())

    if args.dry_run:
        print(progress_line(...))
        time.sleep(0.002)
        successful += 1
        continue

    result = run_git_command([
        "git",
        "commit",
        "--allow-empty",
        "-m",
        msg
    ])

    if result.returncode != 0:
        failed += 1

        print()

        print(
            f"{F.RED}✗ Failed commit {i}{S.RESET_ALL}"
        )

        if result.stderr:
            print(
                f"{F.YELLOW}stderr:{S.RESET_ALL}"
            )
            print(result.stderr.strip())

        if result.stdout:
            print(
                f"{F.YELLOW}stdout:{S.RESET_ALL}"
            )
            print(result.stdout.strip())

        continue

    successful += 1

    print(progress_line(...))

    if args.push and i % PUSH_INTERVAL == 0:
        push_commits(i, args.dry_run)

print("\r" + (" " * 120) + "\r", end="")

if args.push and args.count % PUSH_INTERVAL != 0:
    push_commits(args.count, args.dry_run)

elapsed = time.time() - start_time

rate = successful / elapsed if elapsed > 0 else 0

print(f"{F.BLUE}{'=' * 90}{S.RESET_ALL}")

print(
    f"{F.GREEN}✓ Completed{S.RESET_ALL} "
    f"{F.WHITE}{successful}{S.RESET_ALL} "
    f"{F.GREEN}commits{S.RESET_ALL}"
)

print(
    f"{F.RED}✗ Failed:{S.RESET_ALL} "
    f"{F.WHITE}{failed}{S.RESET_ALL}"
)

print(
    f"{F.CYAN}Time elapsed:{S.RESET_ALL} "
    f"{F.WHITE}{elapsed:.2f}s{S.RESET_ALL}"
)

print(
    f"{F.YELLOW}Average speed:{S.RESET_ALL} "
    f"{F.WHITE}{rate:.2f}{S.RESET_ALL} "
    f"{F.GREEN}commits/s{S.RESET_ALL}"
)

print(
    f"{F.MAGENTA}Finished:{S.RESET_ALL} "
    f"{F.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{S.RESET_ALL}"
)

print(f"{F.BLUE}{'=' * 90}{S.RESET_ALL}")

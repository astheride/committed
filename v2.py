#!/usr/bin/env python3
import argparse
import subprocess
import uuid
import time
from datetime import datetime

try:
    from colorama import init, Fore, Style # Colors = good
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        RESET_ALL = BRIGHT = DIM = ''


PUSH_INTERVAL = 100000000

def push_if_needed(count, args, color_fore, color_style):
    if args.push:
        if args.dry_run:
            print(f"{color_fore.YELLOW}[DRY RUN]{color_style.RESET_ALL} {color_fore.WHITE}git push{color_style.RESET_ALL} {color_fore.CYAN}(after {count} commits){color_style.RESET_ALL}")
        else:
            print(f"{color_fore.BLUE}Pushing commits after {color_fore.WHITE}{count}{color_fore.BLUE}...{color_style.RESET_ALL}")
            subprocess.run(["git", "push"], check=True)
            print(f"{color_fore.GREEN}✓{color_style.RESET_ALL} {color_fore.WHITE}Push completed{color_style.RESET_ALL}")
        print() 

def format_stats_line(i, count, start_time, color_fore, color_style, msg=""):
    """Format and return single-line progress string"""
    current_time = time.time()
    total_elapsed = current_time - start_time
    
    commits_per_sec = i / total_elapsed if total_elapsed > 0 else 0
    eta_seconds = (count - i) / commits_per_sec if commits_per_sec > 0 else 0
    eta_minutes = eta_seconds / 60
    
    progress_percent = (i / count) * 100
    
    bar_width = 20
    filled = int(bar_width * (i / count))
    bar = "█" * filled + "░" * (bar_width - filled)
    
    stats = (
        f"\r{color_fore.CYAN}[{i:>{len(str(count))}}/{count}]{color_style.RESET_ALL} "
        f"{color_fore.GREEN}[{bar}]{color_style.RESET_ALL} "
        f"{color_fore.MAGENTA}{progress_percent:>5.1f}%{color_style.RESET_ALL} "
        f"{color_fore.WHITE}{commits_per_sec:>6.2f}{color_fore.GREEN}(+{commits_per_sec:>4.0f}/s){color_style.RESET_ALL} "
        f"{color_fore.BLUE}ETA:{color_fore.WHITE}{eta_minutes:>4.1f}m{color_style.RESET_ALL} "
        f"{color_fore.YELLOW}{msg[:8]}...{color_style.RESET_ALL}"
    )
    return stats

def get_color_classes(no_color=False):
    """Return color classes based on availability and preference"""
    if no_color or not COLORS_AVAILABLE:
        class NoColorFore:
            RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
        class NoColorStyle:
            RESET_ALL = BRIGHT = DIM = ''
        return NoColorFore(), NoColorStyle()
    else:
        return Fore, Style

def main():
    parser = argparse.ArgumentParser(description="Create multiple git commits with statistics")
    parser.add_argument("count", type=int, help="Number of commits")
    parser.add_argument("-p", "--push", action="store_true", help="Push commits")
    parser.add_argument("--dry-run", action="store_true", help="Show commands only")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()

    color_fore, color_style = get_color_classes(args.no_color)

    if args.count <= 0:
        raise SystemExit(f"{color_fore.RED}Error: Count must be positive{color_style.RESET_ALL}")

    print(f"{color_fore.CYAN}Starting to create {color_fore.WHITE}{args.count}{color_fore.CYAN} commits...{color_style.RESET_ALL}")
    print(f"{color_fore.YELLOW}Push interval: {color_fore.WHITE}every {PUSH_INTERVAL} commits{color_style.RESET_ALL}")
    print(f"{color_fore.GREEN}Time: {color_fore.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{color_style.RESET_ALL}")
    print(f"{color_fore.BLUE}{'=' * 80}{color_style.RESET_ALL}")

    start_time = time.time()

    for i in range(1, args.count + 1):
        msg = str(uuid.uuid4())

        if args.dry_run:
            progress_line = format_stats_line(i, args.count, start_time, color_fore, color_style, "[DRY RUN]")
            print(progress_line, end="", flush=True)
        else:
            try:
                subprocess.run(["git", "commit", "--allow-empty", "-m", msg], 
                             check=True, capture_output=True)
                progress_line = format_stats_line(i, args.count, start_time, color_fore, color_style, msg)
                print(progress_line, end="", flush=True)
            except subprocess.CalledProcessError as e:
                error_line = f"\r{color_fore.RED}✗ Error creating commit {i}: {e}{color_style.RESET_ALL}"
                print(error_line)
                continue

        if i % PUSH_INTERVAL == 0:
            print()
            push_if_needed(i, args, color_fore, color_style)
            print(f"{color_fore.BLUE}{'=' * 80}{color_style.RESET_ALL}")

    print("\r" + " " * 100 + "\r", end="")

    if args.count % PUSH_INTERVAL != 0:
        print()
        push_if_needed(args.count, args, color_fore, color_style)

    total_time = time.time() - start_time
    final_speed = args.count / total_time if total_time > 0 else 0
    
    print(f"{color_fore.BLUE}{'=' * 80}{color_style.RESET_ALL}")
    print(f"{color_fore.GREEN}✓{color_style.RESET_ALL} {color_fore.WHITE}Completed {color_fore.CYAN}{args.count}{color_fore.WHITE} commits in {color_fore.YELLOW}{total_time:.2f}{color_fore.WHITE} seconds{color_style.RESET_ALL}")
    print(f"{color_fore.CYAN}Average speed:{color_style.RESET_ALL} {color_fore.WHITE}{final_speed:.2f}{color_fore.GREEN} commits/second (+{final_speed:.0f}/s){color_style.RESET_ALL}")
    print(f"{color_fore.YELLOW}Finished at:{color_style.RESET_ALL} {color_fore.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{color_style.RESET_ALL}")
    print(f"{color_fore.BLUE}{'=' * 80}{color_style.RESET_ALL}")

if __name__ == "__main__":
    main()

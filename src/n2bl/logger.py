import sys
from tabulate import tabulate
from colorama import Fore, Style, init
init(autoreset=True)

def info(msg):
    print(Fore.GREEN + "[INFO] " + Style.RESET_ALL + str(msg), file=sys.stdout, flush=True)

def warn(msg):
    print(Fore.YELLOW + "[WARN] " + Style.RESET_ALL + str(msg), file=sys.stderr, flush=True)

def error(msg):
    print(Fore.RED + "[ERROR] " + Style.RESET_ALL + str(msg), file=sys.stderr, flush=True)

def print_as_table(items, headers):
    if not items:
        print("(empty)")
        return
    if isinstance(items[0], dict):
        rows = [[i.get(h, "") for h in headers] for i in items]
    else:
        rows = items
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

#!/usr/bin/env python3
"""Subnet Calculator - IPv4 subnetting and VLSM planning in the terminal."""

import argparse
import csv
import itertools
import json
import sys

from calculator import calculate_subnet, iter_split
from vlsm import vlsm_calculate

SUBNET_FIELDS = [
    ("IP Address", "ip"),
    ("Network Address", "network"),
    ("Broadcast", "broadcast"),
    ("Subnet Mask", "subnet_mask"),
    ("Wildcard Mask", "wildcard"),
    ("CIDR", "cidr"),
    ("First Host", "first_host"),
    ("Last Host", "last_host"),
    ("Usable Hosts", "usable_hosts"),
    ("Total Addresses", "total_addresses"),
    ("IP Type", "ip_type"),
    ("Binary Mask", "binary_mask"),
]


def print_subnet(result):
    width = max(len(label) for label, _ in SUBNET_FIELDS)
    print()
    for label, key in SUBNET_FIELDS:
        value = f"/{result[key]}" if key == "cidr" else result[key]
        print(f"  {label:<{width}} : {value}")
    print()


def print_table(headers, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    line = "  ".join("{:<%d}" % w for w in widths)
    print(line.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line.format(*[str(c) for c in row]))


def print_vlsm(result):
    print(f"\n  Base network: {result['network']}\n")
    rows = [
        (s["name"], f"{s['network']}/{s['cidr']}", s["subnet_mask"],
         f"{s['first_host']} - {s['last_host']}", s["broadcast"],
         s["needed_hosts"], s["usable_hosts"], s["wasted"])
        for s in result["subnets"]
    ]
    print_table(["Name", "Network", "Mask", "Host range", "Broadcast",
                 "Needed", "Usable", "Wasted"], rows)
    print(f"\n  Hosts needed : {result['total_needed']}"
          f"\n  Hosts usable : {result['total_allocated']}"
          f"\n  Efficiency   : {result['efficiency']}%"
          f"\n  Addresses    : {result['used_size']} used, {result['free_size']} free"
          f" of {result['total_size']}\n")


def write_vlsm_csv(result, path):
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Network", "CIDR", "Subnet Mask", "First Host", "Last Host",
                        "Broadcast", "Usable Hosts", "Needed", "Wasted"])
            for s in result["subnets"]:
                w.writerow([s["name"], s["network"], f"/{s['cidr']}", s["subnet_mask"],
                            s["first_host"], s["last_host"], s["broadcast"],
                            s["usable_hosts"], s["needed_hosts"], s["wasted"]])
    except OSError as e:
        raise ValueError(f"could not save '{path}': {e.strerror}") from None


def parse_requirements(items):
    """Turn ['Sales=50', 'Eng:25'] into [{'name': 'Sales', 'hosts': 50}, ...].

    Splits on the last '=' or ':' so names like 'VLAN:10=50' keep their separators.
    """
    reqs = []
    for item in items:
        cut = max(item.rfind("="), item.rfind(":"))
        name, count = item[:cut], item[cut + 1:]
        if cut < 0 or not name.strip():
            raise ValueError(f"'{item}' should look like Name=Hosts, e.g. Sales=50")
        try:
            hosts = int(count)
        except ValueError:
            raise ValueError(f"'{count}' is not a number in '{item}'") from None
        if hosts < 1:
            raise ValueError(f"host count must be at least 1 in '{item}'")
        reqs.append({"name": name.strip(), "hosts": hosts})
    return reqs


# ---------- commands ----------

def cmd_subnet(args):
    result = calculate_subnet(" ".join(args.address))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_subnet(result)


def cmd_split(args):
    _, subnets = iter_split(args.network, args.prefix)
    for cidr in subnets:
        print(cidr)


def cmd_vlsm(args):
    result = vlsm_calculate(args.network, parse_requirements(args.requirements))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_vlsm(result)
    if args.csv:
        write_vlsm_csv(result, args.csv)
        print(f"  Saved {args.csv}", file=sys.stderr)


# ---------- interactive mode ----------

MENU = """
  Subnet Calculator
  -----------------
  1) Subnet details   (IP/CIDR or IP + mask)
  2) VLSM plan
  3) Split a network  into equal subnets
  q) Quit
"""


def interactive():
    while True:
        print(MENU)
        try:
            choice = input("  Choose: ").strip().lower()
            if choice in ("q", "quit", "exit"):
                return
            if choice == "1":
                print_subnet(calculate_subnet(input("  IP (e.g. 192.168.1.10/24): ")))
            elif choice == "2":
                network = input("  Base network (e.g. 192.168.0.0/24): ")
                print("  Enter requirements as Name=Hosts, one per line. Blank line to finish.")
                items = []
                while (line := input("  > ").strip()):
                    items.append(line)
                result = vlsm_calculate(network, parse_requirements(items))
                print_vlsm(result)
                path = input("  Save as CSV? Enter a filename or leave blank: ").strip()
                if path:
                    write_vlsm_csv(result, path)
                    print(f"  Saved {path}")
            elif choice == "3":
                network = input("  Network (e.g. 10.0.0.0/16): ")
                prefix = int(input("  New prefix length (e.g. 24): ").lstrip("/"))
                count, subnets = iter_split(network, prefix)
                print(f"\n  {count} subnets:")
                for cidr in itertools.islice(subnets, 64):
                    print(f"    {cidr}")
                if count > 64:
                    print(f"    ... and {count - 64} more")
            else:
                print("  Please choose 1, 2, 3 or q.")
        except ValueError as e:
            print(f"\n  Error: {e}")
        except (EOFError, KeyboardInterrupt):
            print()
            return


def build_parser():
    p = argparse.ArgumentParser(
        prog="subnet-calculator",
        description="IPv4 subnet calculator and VLSM planner. Run with no arguments for interactive mode.")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("subnet", help="show details for an address, e.g. 192.168.1.10/24")
    s.add_argument("address", nargs="+", help="IP/CIDR, IP/mask, or IP followed by mask")
    s.add_argument("--json", action="store_true", help="output JSON")
    s.set_defaults(func=cmd_subnet)

    v = sub.add_parser("vlsm", help="plan subnets, e.g. vlsm 192.168.0.0/24 Sales=50 Eng=25")
    v.add_argument("network", help="base network in CIDR form")
    v.add_argument("requirements", nargs="+", metavar="NAME=HOSTS")
    v.add_argument("--csv", metavar="FILE", help="also write the plan to a CSV file")
    v.add_argument("--json", action="store_true", help="output JSON")
    v.set_defaults(func=cmd_vlsm)

    sp = sub.add_parser("split", help="split a network into equal subnets")
    sp.add_argument("network")
    sp.add_argument("prefix", type=lambda x: int(x.lstrip("/")), help="new prefix length, e.g. 26")
    sp.set_defaults(func=cmd_split)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.command:
        interactive()
        return 0
    try:
        args.func(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

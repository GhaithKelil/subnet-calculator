# Subnet Calculator

A fast, dependency-free command-line tool for IPv4 subnetting and VLSM planning. Pure Python standard library: no installs, no web server, no setup.

## Features

- **Subnet details** from `IP/CIDR`, `IP/mask` or `IP mask`: network, broadcast, mask, wildcard, host range, usable hosts, private/public, binary mask
- **VLSM planner** that allocates the smallest fitting block per requirement, largest first, and reports waste and efficiency
- **Split** a network into equal subnets
- **Export** VLSM plans to CSV or JSON
- **Interactive menu** when run with no arguments
- Correct handling of `/31` (point-to-point, RFC 3021) and `/32` (single host)
- Clear error messages for invalid addresses, masks and plans that do not fit

## Requirements

Python 3.8 or newer. Nothing else.

## Usage

```bash
git clone https://github.com/GhaithKelil/subnet-calculator.git
cd subnet-calculator
python cli.py
```

Running without arguments opens the interactive menu. For scripting, use subcommands.

### Subnet details

```bash
python cli.py subnet 192.168.1.10/24
python cli.py subnet 10.0.0.5 255.255.255.252
python cli.py subnet 172.16.5.9/20 --json
```

```
  IP Address      : 192.168.1.10
  Network Address : 192.168.1.0
  Broadcast       : 192.168.1.255
  Subnet Mask     : 255.255.255.0
  Wildcard Mask   : 0.0.0.255
  CIDR            : /24
  First Host      : 192.168.1.1
  Last Host       : 192.168.1.254
  Usable Hosts    : 254
  Total Addresses : 256
  IP Type         : Private
  Binary Mask     : 11111111.11111111.11111111.00000000
```

### VLSM plan

Pass a base network and `Name=Hosts` requirements:

```bash
python cli.py vlsm 192.168.0.0/24 Sales=50 Eng=25 Mgmt=10 Link=2
python cli.py vlsm 192.168.0.0/24 Sales=50 Eng=25 --csv plan.csv
```

```
Name   Network           Mask             Host range                     Broadcast      Needed  Usable  Wasted
-----  ----------------  ---------------  -----------------------------  -------------  ------  ------  ------
Sales  192.168.0.0/26    255.255.255.192  192.168.0.1 - 192.168.0.62     192.168.0.63   50      62      12
Eng    192.168.0.64/27   255.255.255.224  192.168.0.65 - 192.168.0.94    192.168.0.95   25      30      5
Mgmt   192.168.0.96/28   255.255.255.240  192.168.0.97 - 192.168.0.110   192.168.0.111  10      14      4
Link   192.168.0.112/30  255.255.255.252  192.168.0.113 - 192.168.0.114  192.168.0.115  2       2       0

  Hosts needed : 87
  Hosts usable : 108
  Efficiency   : 80.6%
  Addresses    : 116 used, 140 free of 256
```

### Split a network

```bash
python cli.py split 10.0.0.0/24 26
```

## How it works

- **Subnetting**: addresses are treated as 32-bit integers and the mask gives the network prefix. Usable hosts are `2^n - 2` for `n` host bits (`2` for `/31`, `1` for `/32`).
- **VLSM**: requirements are sorted largest first. Each gets the smallest block with `ceil(log2(hosts + 2))` host bits, placed right after the previous block so every subnet stays aligned. If a block would pass the end of the base network, the plan is rejected.

## Project structure

```
subnet-calculator/
├── cli.py          # Command-line interface and interactive menu
├── calculator.py   # Subnet maths
├── vlsm.py         # VLSM allocation
└── readme.md
```

## Author

Ghaith Kelil, IT Engineering student at Metropolia University of Applied Sciences.

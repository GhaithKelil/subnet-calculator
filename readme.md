<div align="center">

# 🧮 Subnet Calculator

**Subnetting and VLSM planning, straight from your terminal.**
No installs. No web server. Just Python and one command.

![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Tests](https://img.shields.io/badge/tests-11%20passing-brightgreen)
![License](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

</div>

---

Ever stared at `172.16.5.9/20` and needed the broadcast address *now*? Or had to carve a `/24` into five departments without wasting half of it? This tool answers both in under a second.

```console
$ python cli.py vlsm 192.168.0.0/24 Sales=50 Eng=25 Mgmt=10 Link=2

Name   Network           Mask             Host range                     Broadcast      Needed  Usable  Wasted
-----  ----------------  ---------------  -----------------------------  -------------  ------  ------  ------
Sales  192.168.0.0/26    255.255.255.192  192.168.0.1 - 192.168.0.62     192.168.0.63   50      62      12
Eng    192.168.0.64/27   255.255.255.224  192.168.0.65 - 192.168.0.94    192.168.0.95   25      30      5
Mgmt   192.168.0.96/28   255.255.255.240  192.168.0.97 - 192.168.0.110   192.168.0.111  10      14      4
Link   192.168.0.112/30  255.255.255.252  192.168.0.113 - 192.168.0.114  192.168.0.115  2       2       0

  Efficiency   : 80.6%
  Addresses    : 116 used, 140 free of 256
```

## ✨ What it does

| | |
|---|---|
| 🔍 **Subnet details** | Network, broadcast, mask, wildcard, host range, usable hosts, private or public, binary mask |
| 📐 **VLSM planner** | Smallest block per requirement, largest first, with waste and efficiency reported |
| ✂️ **Network splitter** | Cut any network into equal subnets |
| 📤 **Export** | CSV for spreadsheets, JSON for scripts |
| 💬 **Interactive menu** | Run with no arguments and just answer the prompts |
| 🛡️ **Careful edge cases** | `/31` point-to-point (RFC 3021), `/32` host routes, and plans that don't fit are all handled |

## 🚀 Quick start

```bash
git clone https://github.com/GhaithKelil/subnet-calculator.git
cd subnet-calculator
python cli.py
```

You only need Python 3.8 or newer. There is nothing to `pip install`.

## 📖 Usage

### Subnet details

Any of these input styles work:

```bash
python cli.py subnet 192.168.1.10/24
python cli.py subnet 10.0.0.5 255.255.255.252
python cli.py subnet 172.16.5.9/255.255.240.0 --json
```

```console
$ python cli.py subnet 192.168.1.10/24

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

Give a base network and `Name=Hosts` pairs. Order doesn't matter, the tool sorts them.

```bash
python cli.py vlsm 10.0.0.0/22 Office=400 Wifi=200 Servers=30 Printers=10
python cli.py vlsm 10.0.0.0/22 Office=400 Wifi=200 --csv plan.csv
```

If the requirements don't fit, you get a clear message instead of a broken plan:

```console
$ python cli.py vlsm 192.168.0.0/26 A=50 B=30
Error: not enough space in 192.168.0.0/26 for 'B' (30 hosts)
```

### Split a network

```console
$ python cli.py split 10.0.0.0/24 26
10.0.0.0/26
10.0.0.64/26
10.0.0.128/26
10.0.0.192/26
```

### Interactive mode

```console
$ python cli.py

  Subnet Calculator
  -----------------
  1) Subnet details   (IP/CIDR or IP + mask)
  2) VLSM plan
  3) Split a network  into equal subnets
  q) Quit
```

## 🧠 How it works

**Subnetting.** An IPv4 address is just a 32-bit number. The mask decides where the network part ends and the host part begins. With `n` host bits you get `2ⁿ - 2` usable hosts (the all-zeros and all-ones addresses are reserved), except `/31` which gives 2 and `/32` which gives 1.

**VLSM.** Fixed-size subnetting wastes addresses. VLSM gives each department only what it needs:

1. Sort requirements from largest to smallest.
2. For each one, pick the smallest block with `⌈log₂(hosts + 2)⌉` host bits.
3. Place it right after the previous block. Largest-first keeps every block aligned on its natural boundary, so nothing overlaps.
4. If a block would run past the end of the base network, stop and report it.

## 🧪 Tests

```bash
python -m unittest -v
```

11 tests cover input formats, `/31` and `/32`, invalid input, splitting, block sizing, ordering, overlap checks and oversized plans.

## 🗂️ Project structure

```
subnet-calculator/
├── cli.py            # command-line interface + interactive menu
├── calculator.py     # subnet maths (pure functions)
├── vlsm.py           # VLSM allocation
├── test_subnet.py    # unit tests
└── readme.md
```

The maths lives in `calculator.py` and `vlsm.py` with no printing, so you can import it into your own scripts:

```python
from calculator import calculate_subnet
print(calculate_subnet("192.168.1.10/24")["broadcast"])   # 192.168.1.255
```

## 👤 Author

**Ghaith Kelil**, IT Engineering student at Metropolia University of Applied Sciences.

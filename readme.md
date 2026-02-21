# Subnet Calculator

A high-precision networking tool for IP subnetting and VLSM calculations.
Built to help plan networks with minimal address waste.

---

## Features

* **Standard Subnetting**
  Calculate network address, broadcast address, and usable host range using CIDR.

* **VLSM Engine**
  Allocates subnets based on different host needs to save address space.

* **Modern UI**
  Clean and structured interface with a dark mode style.

* **Real-Time Validation**
  Prevents overlapping subnets and invalid input.

---

## Tech Stack

* **Backend**: Python 3.11, Flask
* **Frontend**: HTML5, CSS3
* **Environment**: Python virtual environment (venv)

---

## Project Structure

```text
subnet-calculator/
├── app.py              # Flask application entry point
├── calculator.py       # Standard subnetting logic
├── vlsm.py             # VLSM calculation logic
├── templates/
│   └── index.html      # Main UI
├── requirements.txt    # Dependencies
└── .gitignore          # Ignore venv and cache files
```

---

## Installation and Setup

Make sure Python is installed.

### 1. Clone the repository

```bash
git clone https://github.com/GhaithKelil/subnet-calculator.git
cd subnet-calculator
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows**

```bash
.\venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open your browser and go to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Logic Overview

### Subnetting Mathematics

IPv4 addresses are converted into 32-bit binary values.
A subnet mask is applied to find the network prefix.
Usable hosts are calculated with:

```
2^n - 2
```

Where `n` is the number of host bits.

### VLSM Optimization

The VLSM module uses a largest-first strategy.

* Subnets are sorted by required host count.
* Each subnet gets the smallest possible CIDR block.
* The next subnet starts right after the previous broadcast address.

---

## Developer

**Ghaith Kelil**
IT Engineering student at Metropolia University of Applied Sciences

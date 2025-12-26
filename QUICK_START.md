# Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

#### Windows (Easy Way)
Simply double-click or run:
```bash
run_server.bat
```
This will automatically install dependencies and start the server.

#### Manual Installation
```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run tests (optional)
python tests/test_cpu.py

# Start server
python manage.py runserver
```

### Access the Simulator
Open your browser and navigate to:
```
http://localhost:8000
```

## 🎮 Using the Simulator

### Interface Overview

The simulator has 6 main panels:

| Panel | Description |
|-------|-------------|
| **Assembly Editor** | Write your assembly code here |
| **Machine Code** | View compiled hex/binary output |
| **Pipeline Timeline** | Visual instruction flow through stages |
| **Pipeline Stages** | Current stage contents and hazard info |
| **Control Signals** | 8-bit control bus values |
| **Registers & Memory** | CPU state (r0-r7 and data memory) |

### Control Buttons

| Button | Action |
|--------|--------|
| **COMPILE** | Format and compile code (doesn't load) |
| **LOAD** | Compile and load program into CPU |
| **STEP** | Execute one clock cycle |
| **RUN** | Continuous execution at set speed |
| **PAUSE** | Stop continuous execution |
| **RESET** | Reset CPU to initial state |

### Speed Control
Use the slider to adjust execution speed (1-100 Hz).

## 📝 Writing Assembly Code

### Instruction Set

#### R-Type Instructions
```assembly
add rd, rs, rt    # rd = rs + rt
sub rd, rs, rt    # rd = rs - rt
and rd, rs, rt    # rd = rs & rt
or rd, rs, rt     # rd = rs | rt
xor rd, rs, rt    # rd = rs ^ rt
slt rd, rs, rt    # rd = (rs < rt) ? 1 : 0
div rd, rs, rt    # rd = rs / rt
```

#### I-Type Instructions
```assembly
addi rt, rs, imm  # rt = rs + imm
lw rt, imm(rs)    # rt = mem[rs + imm]
sw rt, imm(rs)    # mem[rs + imm] = rt
beq rs, rt, imm   # if (rs == rt) PC += imm
j imm             # PC += imm
jal imm           # r7 = PC + 1; PC += imm
jr rs             # PC = rs
```

### Quick Examples

#### 1. Simple Arithmetic
```assembly
addi r1, r0, 5    # r1 = 5
addi r2, r0, 3    # r2 = 3
add r3, r1, r2    # r3 = 8
```

#### 2. Memory Access
```assembly
addi r1, r0, 42   # r1 = 42
sw r1, 0(r0)      # mem[0] = 42
lw r2, 0(r0)      # r2 = mem[0]
```

#### 3. Loop (Sum 1 to 5)
```assembly
addi r1, r0, 0    # sum = 0
addi r2, r0, 1    # i = 1
addi r3, r0, 6    # limit = 6
add r1, r1, r2    # sum += i
addi r2, r2, 1    # i++
beq r2, r3, 2     # if i == 6, exit
j -3              # loop
nop               # done
```

## 🔧 Understanding the Pipeline

### 5 Pipeline Stages

```
IF → ID → EX → MEM → WB
```

| Stage | Description |
|-------|-------------|
| **IF** | Fetch instruction from memory |
| **ID** | Decode instruction, read registers |
| **EX** | Execute ALU operation |
| **MEM** | Access data memory |
| **WB** | Write result back to register |

### Hazard Indicators

| Indicator | Meaning |
|-----------|---------|
| **Stall** | Pipeline stalled (load-use hazard) |
| **Forward A/B** | Data forwarding source (00=none, 01=MEM/WB, 10=EX/MEM) |
| **PC Source** | Branch/Jump taken |
| **Flush** | Instructions being flushed |

## 📁 Example Programs

Check the `examples/` folder:
- `fibonacci.asm` - Fibonacci sequence generator
- `sum_array.asm` - Array summation
- `hazards_demo.asm` - Demonstrates all hazard types

## ❓ Troubleshooting

### "Connection Failed"
- Make sure the server is running
- Check if port 8000 is available
- Try refreshing the browser

### "Assembly Error"
- Check instruction syntax
- Verify register names (r0-r7)
- Ensure immediate values are in range (-32 to +31)

### Pipeline Not Updating
- Click LOAD after writing code
- Use STEP or RUN to advance cycles

## 🎓 Tips for Learning

1. **Start Simple**: Begin with basic arithmetic before loops
2. **Watch the Timeline**: See how instructions flow through stages
3. **Observe Hazards**: Load-use stalls and forwarding are visible
4. **Use STEP**: Single-stepping helps understand each cycle
5. **Check Registers**: Verify results match expectations

Happy Simulating! ⚡

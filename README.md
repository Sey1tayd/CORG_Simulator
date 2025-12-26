# 16-bit CPU Simulator - 5-Stage Pipeline

A comprehensive web-based simulator for a 5-stage pipelined 16-bit CPU with hazard detection, data forwarding, and real-time visualization.

## Features

- **5-Stage Pipeline**: IF (Instruction Fetch), ID (Instruction Decode), EX (Execute), MEM (Memory), WB (Write Back)
- **Hazard Handling**:
  - Data forwarding (EX/MEM and MEM/WB to EX stage)
  - Load-use stall detection
  - Control hazard flushing (branch/jump)
  - Store-data forwarding
  - Register file write-first bypass
- **16-bit ISA** with R-type and I-type instructions
- **Dark Theme UI** with real-time pipeline visualization
- **Interactive Timeline** with hover tooltips showing detailed stage information
- **WebSocket-based** real-time updates

## Architecture

### Register File
- 8 registers (r0-r7), each 16-bit
- r0 is hardwired to 0
- Write-first bypass for same-cycle read-after-write

### Memory
- Instruction Memory: 256 words (16-bit each)
- Data Memory: 256 words (16-bit each, word-addressed)

### Pipeline Stages

1. **IF (Instruction Fetch)**: Fetch instruction from memory, update PC
2. **ID (Instruction Decode)**: Decode instruction, read registers, generate control signals
3. **EX (Execute)**: ALU operations, branch/jump target calculation, forwarding logic
4. **MEM (Memory Access)**: Load/store operations
5. **WB (Write Back)**: Write results to register file

## ISA (Instruction Set Architecture)

### R-Type Instructions (opcode = 0000)
Format: `[opcode:4][rs:3][rt:3][rd:3][func:3]`

| Instruction | Func | Description |
|-------------|------|-------------|
| `add rd, rs, rt` | 000 | rd = rs + rt |
| `sub rd, rs, rt` | 001 | rd = rs - rt |
| `and rd, rs, rt` | 010 | rd = rs & rt |
| `or rd, rs, rt` | 011 | rd = rs \| rt |
| `xor rd, rs, rt` | 100 | rd = rs ^ rt |
| `slt rd, rs, rt` | 101 | rd = (rs < rt) ? 1 : 0 (signed) |
| `div rd, rs, rt` | 110 | rd = rs / rt (div-by-zero safe) |

### I-Type Instructions
Format: `[opcode:4][rs:3][rt:3][imm6:6]`

| Instruction | Opcode | Description |
|-------------|--------|-------------|
| `addi rt, rs, imm` | 0001 | rt = rs + imm |
| `lw rt, imm(rs)` | 0010 | rt = mem[rs + imm] |
| `sw rt, imm(rs)` | 0011 | mem[rs + imm] = rt |
| `beq rs, rt, imm` | 0100 | if (rs == rt) PC = PC + imm |
| `j imm` | 0101 | PC = PC + imm |
| `jal imm` | 0110 | r7 = PC + 1; PC = PC + imm |
| `jr rs` | 0111 | PC = rs |

**Note**: `imm6` is signed 6-bit (-32 to +31), sign-extended to 16-bit.

## Control Signals

8-bit control bus (Ctrl[0:7]):
- **Bit 0**: RegDst - Destination register selection (0=rt, 1=rd)
- **Bit 1**: AluSrc - ALU operand B source (0=register, 1=immediate)
- **Bit 2**: MemToReg - Write-back data source (0=ALU, 1=memory)
- **Bit 3**: RegWrite - Enable register write
- **Bit 4**: MemRead - Enable memory read
- **Bit 5**: MemWrite - Enable memory write
- **Bit 6**: Bench - Branch control
- **Bit 7**: Jump - Jump control

## Installation

### Prerequisites
- Python 3.11+
- pip

### Quick Start (Windows)

Simply run:
```bash
run_server.bat
```

This will install dependencies, run tests, and start the server.

### Manual Setup

1. Clone or extract the project:
```bash
cd Sim_Django
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run tests (optional):
```bash
python tests/test_cpu.py
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Open your browser to: `http://localhost:8000`

The server uses WebSockets, so make sure your firewall allows the connection.

## Usage

### Interface Layout

The UI is divided into 6 panels:

1. **Assembly Code** (top-left): Write assembly code, assemble, and load into CPU
2. **Machine Code** (top-center): View hex machine code with PC highlighting
3. **CPU Info** (top-right): Real-time CPU state (cycle, PC, control signals, hazards)
4. **Pipeline Timeline** (bottom-left): Visual timeline showing instruction flow through stages
5. **Register File** (bottom-right top): Current register values
6. **Data Memory** (bottom-right bottom): Non-zero memory locations

### Controls

- **Assemble & Load**: Assemble the code in the editor and load into instruction memory
- **Step**: Execute one clock cycle
- **Run**: Continuous execution at specified Hz
- **Pause**: Stop continuous execution
- **Reset**: Reset CPU to initial state
- **Hz Slider**: Adjust execution speed (1-100 Hz)

### Pipeline Timeline

- Shows instructions flowing through pipeline stages (IF, ID, EX, MEM, WB)
- Color-coded by stage:
  - **IF**: Blue
  - **ID**: Green
  - **EX**: Yellow
  - **MEM**: Purple
  - **WB**: Red
- Hover over any cell to see detailed information about that instruction at that stage
- Auto-scrolls to keep current cycle centered

### Example Programs

#### Simple Arithmetic
```assembly
# Add two numbers
addi r1, r0, 5
addi r2, r0, 3
add r3, r1, r2
```

#### Load/Store
```assembly
# Store and load
addi r1, r0, 10
sw r1, 0(r0)
lw r2, 0(r0)
```

#### Branching
```assembly
# Conditional branch
addi r1, r0, 5
addi r2, r0, 5
beq r1, r2, 2    # Skip next 2 instructions
addi r3, r0, 1
addi r4, r0, 2
addi r5, r0, 3   # This executes
```

#### Loop Example
```assembly
# Sum from 1 to 5
addi r1, r0, 0   # sum
addi r2, r0, 1   # counter
addi r3, r0, 5   # limit
add r1, r1, r2   # sum += counter
addi r2, r2, 1   # counter++
beq r2, r3, 2    # if counter != limit, continue
j -3             # jump back to add
nop              # done
```

#### Function Call (JAL/JR)
```assembly
# Call a function
addi r1, r0, 5
jal 2            # Call function at PC+2
addi r2, r0, 10  # After return
j 3              # Skip function
addi r1, r1, r1  # Function: double r1
jr r7            # Return
```

## Testing

Run the CPU core tests:

```bash
python tests/test_cpu.py
```

Tests cover:
- Basic instruction execution
- Load/Store operations
- Data forwarding
- Load-use stall detection
- Branch/Jump control hazards
- Division by zero safety

## Architecture Details

### Hazard Detection

**Load-Use Stall**:
```
if (ID_EX.MemRead and 
    ((ID_EX.Rt == IF_ID.Rs) or (ID_EX.Rt == IF_ID.Rt))):
    stall pipeline (PCWrite=0, IF_ID_Write=0, ID_EX_Flush=1)
```

**Data Forwarding**:
```
ForwardA/B = 10 (from EX/MEM) if:
    EX_MEM.RegWrite and EX_MEM.Rd == ID_EX.Rs/Rt
    
ForwardA/B = 01 (from MEM/WB) if:
    MEM_WB.RegWrite and MEM_WB.Rd == ID_EX.Rs/Rt
```

**Control Hazard Flush**:
```
if (PcSrc == 1):  # Branch taken or Jump
    flush IF/ID and ID/EX stages (insert bubbles)
```

### Pipeline Registers

- **IF/ID**: PC+1, Instruction
- **ID/EX**: PC, ReadData1, ReadData2, Imm, Rs, Rt, DestReg, Ctrl, ALUctr
- **EX/MEM**: BranchTarget, Zero, ALUResult, ReadData2, DestReg, Ctrl
- **MEM/WB**: MemData, ALUResult, DestReg, Ctrl

## Project Structure

```
Sim_Django/
├── cpu_core/              # CPU simulation core (Django-independent)
│   ├── __init__.py
│   ├── isa.py            # ISA definitions
│   ├── alu.py            # ALU implementation
│   ├── hazard.py         # Hazard detection and forwarding
│   ├── pipeline_regs.py  # Pipeline register classes
│   ├── cpu.py            # Main CPU class
│   ├── assembler.py      # Assembly to machine code
│   └── disassembler.py   # Machine code to assembly
├── cpu_sim/              # Django app
│   ├── consumers.py      # WebSocket consumer
│   ├── routing.py        # WebSocket routing
│   ├── views.py          # HTTP views
│   ├── urls.py           # URL configuration
│   ├── templates/
│   │   └── cpu_sim/
│   │       └── index.html
│   └── static/
│       └── cpu_sim.js    # Frontend JavaScript
├── sim_django/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── tests/
│   └── test_cpu.py       # Unit tests
├── requirements.txt
├── manage.py
└── README.md
```

## Technical Notes

### Division by Zero
The DIV instruction is safe: division by zero returns 0 without crashing.

### Register r0
r0 is always 0. Writes to r0 are ignored.

### PC Addressing
PC is an instruction index (not byte address). PC+1 refers to the next instruction.

### Signed/Unsigned
All operations treat data as signed 16-bit two's complement unless noted otherwise.

### Memory Addressing
Memory is word-addressed: address N refers to the Nth 16-bit word.

## Performance

- Supports up to 100 Hz execution speed
- Real-time WebSocket updates
- Efficient timeline rendering with auto-scroll

## Browser Compatibility

- Chrome/Edge: Recommended
- Firefox: Supported
- Safari: Supported

## License

Educational project - free to use and modify.

## Credits

Built with:
- Django 4.2
- Django Channels 4.0
- Pure JavaScript (no frameworks)
- CSS Grid Layout

#   C O R G _ S i m u l a t o r  
 
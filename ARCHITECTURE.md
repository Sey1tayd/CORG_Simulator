# CPU Architecture Documentation

## Overview

This document provides detailed technical information about the 16-bit 5-stage pipelined CPU implementation.

## Pipeline Architecture

### Stage 1: IF (Instruction Fetch)
**Purpose**: Fetch instruction from memory and update PC

**Operations**:
1. Read instruction from `instr_mem[PC]`
2. Calculate `PC+1`
3. Check for hazards (load-use stall)
4. Update IF/ID register (if not stalled)
5. Update PC (if not stalled and no branch/jump)

**Hazard Handling**:
- If load-use hazard detected: stall (don't update PC or IF/ID)
- If branch/jump taken: flush IF/ID (insert NOP)

**Pipeline Register Output (IF/ID)**:
- `pc_plus_1`: Next sequential PC
- `instr`: 16-bit instruction

### Stage 2: ID (Instruction Decode)
**Purpose**: Decode instruction, read registers, generate control signals

**Operations**:
1. Extract fields from instruction (opcode, rs, rt, rd, func, imm)
2. Generate control signals based on opcode
3. Determine ALU control signal
4. Read register file (with WB bypass)
5. Sign-extend immediate
6. Determine destination register (RegDst mux, JAL special case)
7. Check for flush condition

**Control Signal Generation**:
```
OPCODE → ControlUnit → 8-bit control bus
         ↓
    [RegDst|AluSrc|MemToReg|RegWrite|MemRead|MemWrite|Bench|Jump]
```

**Pipeline Register Output (ID/EX)**:
- `pc`: PC of this instruction
- `read_data1`, `read_data2`: Register values
- `imm`: Sign-extended immediate
- `rs`, `rt`: Source register numbers
- `dest_reg`: Destination register
- `ctrl`: Control signals
- `alu_ctrl`: ALU operation code

### Stage 3: EX (Execute)
**Purpose**: Execute ALU operation, calculate branch target, handle forwarding

**Operations**:
1. Compute forwarding signals (ForwardA, ForwardB)
2. Select ALU operand A (with forwarding)
3. Select ALU operand B (with forwarding, then AluSrc mux)
4. Execute ALU operation
5. Calculate branch target: `PC + imm`
6. Determine branch/jump taken (PcSrc)
7. Handle JAL (return address)
8. Handle JR (register jump)
9. Update PC if branch/jump taken

**Forwarding Logic**:
```
ForwardA = 10 if EX/MEM.RegWrite && EX/MEM.Rd == ID/EX.Rs
ForwardA = 01 if MEM/WB.RegWrite && MEM/WB.Rd == ID/EX.Rs
ForwardA = 00 otherwise

Same for ForwardB with ID/EX.Rt
```

**ALU Operand Selection**:
```
ALU.A = ForwardA==10 ? EX/MEM.ALUResult :
        ForwardA==01 ? WriteData_WB :
                       ID/EX.ReadData1

RegB  = ForwardB==10 ? EX/MEM.ALUResult :
        ForwardB==01 ? WriteData_WB :
                       ID/EX.ReadData2

ALU.B = AluSrc ? ID/EX.Imm : RegB
```

**Branch/Jump Logic**:
```
BranchTaken = Bench && Zero
PcSrc = BranchTaken || Jump

if PcSrc:
    if JR (Jump && AluSrc):
        PC = ReadData1 (register value)
    else:
        PC = BranchTarget (PC + imm)
```

**Pipeline Register Output (EX/MEM)**:
- `branch_target`: PC + imm
- `zero`: ALU zero flag
- `alu_result`: ALU output (or return address for JAL)
- `read_data2`: Store data (forwarded)
- `dest_reg`: Destination register
- `ctrl`: Control signals

### Stage 4: MEM (Memory Access)
**Purpose**: Read from or write to data memory

**Operations**:
1. Extract address from ALU result
2. If MemRead: read from `data_mem[address]`
3. If MemWrite: write to `data_mem[address]`

**Memory Addressing**:
- Word-addressed (not byte-addressed)
- Address = ALU result & 0xFF (8-bit address space)
- Each word is 16 bits

**Pipeline Register Output (MEM/WB)**:
- `mem_data`: Data read from memory
- `alu_result`: ALU result (passed through)
- `dest_reg`: Destination register
- `ctrl`: Control signals

### Stage 5: WB (Write Back)
**Purpose**: Write result to register file

**Operations**:
1. Select write data (MemToReg mux)
2. If RegWrite: write to register file
3. Provide bypass data for ID stage

**Write Data Selection**:
```
WriteData = MemToReg ? MEM/WB.MemData : MEM/WB.ALUResult
```

**Register File Update**:
```
if RegWrite && DestReg != 0:
    RegFile[DestReg] = WriteData
```

## Hazard Handling

### 1. Data Hazards - Forwarding

**EX Hazard (EX-EX forwarding)**:
```
Instruction 1: add r1, r2, r3  (writes r1 in WB)
Instruction 2: add r4, r1, r5  (needs r1 in EX)
               ↑
          Forward from EX/MEM
```

**MEM Hazard (MEM-EX forwarding)**:
```
Instruction 1: add r1, r2, r3  (writes r1 in WB)
Instruction 2: nop
Instruction 3: add r4, r1, r5  (needs r1 in EX)
               ↑
          Forward from MEM/WB
```

**Priority**: EX/MEM forwarding takes priority over MEM/WB forwarding.

### 2. Data Hazards - Load-Use Stall

**Problem**:
```
Cycle:    1    2    3    4    5    6
lw r1:   IF   ID   EX  MEM   WB
add r2:       IF   ID  [STALL] EX  MEM
                      ↑
              Data not ready yet
```

**Solution**: Insert 1-cycle bubble
```
if ID/EX.MemRead && 
   (ID/EX.Rt == IF/ID.Rs || ID/EX.Rt == IF/ID.Rt):
    PCWrite = 0       (don't update PC)
    IF/ID_Write = 0   (don't update IF/ID)
    ID/EX_Flush = 1   (insert bubble in ID/EX)
```

### 3. Control Hazards - Branch/Jump Flush

**Problem**: Instructions after branch/jump are fetched before decision is made.

**Solution**: Flush IF/ID and ID/EX when branch/jump taken
```
Cycle:    1    2    3    4    5
beq:     IF   ID   EX  MEM   WB
                   ↑
              Decision made here
instr+1:      IF   ID [FLUSH]
instr+2:           IF [FLUSH]
target:                 IF   ID
```

**Implementation**:
```
if PcSrc:
    IF/ID.Instr = 0  (NOP)
    ID/EX.Ctrl = 0   (bubble)
```

### 4. Register File Bypass

**Same-cycle read-after-write**:
```
Cycle:    1    2    3    4    5
add r1:  IF   ID   EX  MEM   WB (writes r1)
sub r2:                      IF   ID (reads r1)
                                  ↑
                            Bypass from WB
```

**Implementation**: Check in ID stage if WB is writing to the register being read.

## Control Signals Detail

### 8-bit Control Bus

| Bit | Name | Function |
|-----|------|----------|
| 0 | RegDst | 0=rt, 1=rd as destination |
| 1 | AluSrc | 0=register, 1=immediate for ALU.B |
| 2 | MemToReg | 0=ALU result, 1=memory data for write-back |
| 3 | RegWrite | 1=write to register file |
| 4 | MemRead | 1=read from memory |
| 5 | MemWrite | 1=write to memory |
| 6 | Bench | 1=branch instruction |
| 7 | Jump | 1=jump instruction |

### Control Signal Truth Table

| Instruction | RegDst | AluSrc | MemToReg | RegWrite | MemRead | MemWrite | Bench | Jump |
|-------------|--------|--------|----------|----------|---------|----------|-------|------|
| R-type | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| ADDI | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| LW | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| SW | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| BEQ | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| J | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| JAL | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 |
| JR | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |

## ALU Operations

| ALU Control | Operation | Description |
|-------------|-----------|-------------|
| 000 | ADD | A + B |
| 001 | SUB | A - B |
| 010 | AND | A & B |
| 011 | OR | A \| B |
| 100 | XOR | A ^ B |
| 101 | SLT | (A < B) ? 1 : 0 (signed) |
| 110 | DIV | A / B (div-by-zero returns 0) |
| 111 | Reserved | NOP |

## Special Cases

### JAL (Jump and Link)
1. In ID: Force `dest_reg = 7` (r7)
2. In EX: Set `ALUResult = PC + 1` (return address)
3. PC updated to `PC + imm`
4. In WB: Write return address to r7

### JR (Jump Register)
1. Control: `Jump=1, AluSrc=1` (distinguishes from J)
2. In EX: PC updated to `ReadData1` (register value)
3. No register write

### DIV by Zero
- If divisor (B) is zero, ALU returns 0
- No exception or crash

### r0 Hardwired to Zero
- Reads always return 0
- Writes are ignored
- Still participates in hazard detection (though unnecessary)

## Performance Characteristics

### CPI (Cycles Per Instruction)
- **Ideal**: 1.0 (with perfect pipeline)
- **With hazards**:
  - Load-use: +1 cycle per occurrence
  - Branch taken: +2 cycles (2 instructions flushed)
  - Jump: +2 cycles

### Throughput
- **Maximum**: 1 instruction per cycle (after pipeline fills)
- **Pipeline depth**: 5 stages
- **Latency**: 5 cycles for single instruction

### Example Performance

```assembly
addi r1, r0, 5    # Cycle 1-5
addi r2, r0, 3    # Cycle 2-6 (overlapped)
add r3, r1, r2    # Cycle 3-7 (forwarding, no stall)
```

Total: 7 cycles for 3 instructions = 2.33 CPI (includes pipeline fill)

## Implementation Notes

### Pipeline Register Updates
- All pipeline registers update simultaneously at clock edge
- Updates happen in reverse order (WB→MEM→EX→ID→IF) to simulate parallelism

### Forwarding Priority
1. EX/MEM (most recent)
2. MEM/WB (older)
3. ID/EX (no forwarding)

### Stall vs Flush
- **Stall**: Hold pipeline registers, don't advance PC
- **Flush**: Insert NOP (zero control signals), advance normally

### Memory Model
- **Instruction memory**: Read-only, 256 words
- **Data memory**: Read/write, 256 words
- **Register file**: 8 registers × 16 bits
- All memories are word-addressed (not byte-addressed)


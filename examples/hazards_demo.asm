# Pipeline Hazards Demonstration
# This program demonstrates various pipeline hazards:
# - Data forwarding (EX-EX and MEM-EX)
# - Load-use stall
# - Control hazards (branch/jump)

# ===== Part 1: Data Forwarding Demo =====
# EX-EX Forwarding: Result needed in next instruction
addi r1, r0, 10      # r1 = 10
add r2, r1, r1       # r2 = r1 + r1 (forwarding from EX/MEM)
add r3, r2, r1       # r3 = r2 + r1 (forwarding from EX/MEM)

# MEM-EX Forwarding: Result needed 2 instructions later
addi r4, r0, 5       # r4 = 5
nop                  # Creates gap
add r5, r4, r1       # r5 = r4 + r1 (forwarding from MEM/WB)

# ===== Part 2: Load-Use Stall Demo =====
# Load followed by immediate use (causes stall)
sw r3, 0(r0)         # Store r3 to mem[0]
lw r6, 0(r0)         # Load from mem[0] into r6
add r7, r6, r1       # r7 = r6 + r1 (STALL inserted here)

# ===== Part 3: Branch Hazard Demo =====
# Conditional branch (control hazard)
addi r1, r0, 5       # r1 = 5
addi r2, r0, 5       # r2 = 5
beq r1, r2, 2        # Branch if r1 == r2 (taken - flush 2 instructions)
addi r3, r0, 99      # This gets flushed
addi r4, r0, 88      # This gets flushed
addi r5, r0, 42      # This executes (branch target)

# ===== Part 4: Jump Hazard Demo =====
# Unconditional jump (control hazard)
j 3                  # Jump forward 3 (target = PC + 3, skip next 2 instructions)
addi r6, r0, 77      # Flushed (was in ID when jump executed)
addi r7, r0, 66      # Flushed (was in IF when jump executed)
add r1, r1, r5       # Executes after jump (target)

# ===== End =====
sw r1, 1(r0)         # Store final result
halt

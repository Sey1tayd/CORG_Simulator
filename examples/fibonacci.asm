# Fibonacci Sequence Generator
# Calculates first 8 Fibonacci numbers and stores in memory
# F(0)=0, F(1)=1, F(2)=1, F(3)=2, F(4)=3, F(5)=5, F(6)=8, F(7)=13

# Initialize registers
addi r1, r0, 0      # r1 = F(n-2) = 0
addi r2, r0, 1      # r2 = F(n-1) = 1
addi r3, r0, 0      # r3 = memory address pointer
addi r4, r0, 6      # r4 = loop counter (6 more iterations after storing first 2)

# Store first two Fibonacci numbers
sw r1, 0(r0)        # mem[0] = 0 (F(0))
sw r2, 1(r0)        # mem[1] = 1 (F(1))
addi r3, r0, 2      # Start storing from address 2

# Loop: Calculate next Fibonacci number
add r5, r1, r2      # r5 = F(n) = F(n-2) + F(n-1)
sw r5, 0(r3)        # Store F(n) in memory
add r1, r0, r2      # r1 = F(n-1) (shift values)
add r2, r0, r5      # r2 = F(n) (shift values)
addi r3, r3, 1      # Increment memory address
addi r4, r4, -1     # Decrement counter
beq r4, r0, 2       # If counter == 0, exit loop
j -7                # Jump back to loop start

# End - Results in memory[0-7]: 0, 1, 1, 2, 3, 5, 8, 13
halt

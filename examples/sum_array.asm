# Sum Array Elements
# Initializes an array with values and calculates the sum
# Array: [5, 10, 15, 20, 25] at mem[10-14]
# Sum stored at mem[0]

# Initialize array elements in memory
addi r1, r0, 5       # Value 5
sw r1, 10(r0)        # mem[10] = 5

addi r1, r0, 10      # Value 10
sw r1, 11(r0)        # mem[11] = 10

addi r1, r0, 15      # Value 15
sw r1, 12(r0)        # mem[12] = 15

addi r1, r0, 20      # Value 20
sw r1, 13(r0)        # mem[13] = 20

addi r1, r0, 25      # Value 25
sw r1, 14(r0)        # mem[14] = 25

# Setup for summation
addi r2, r0, 0       # r2 = sum accumulator
addi r3, r0, 10      # r3 = current address (start at 10)
addi r4, r0, 15      # r4 = end address (15, exclusive)

# Sum loop
lw r1, 0(r3)         # Load value from memory
add r2, r2, r1       # Add to sum
addi r3, r3, 1       # Increment address
beq r3, r4, 2        # If address == end, exit loop
j -4                 # Jump back to loop start

# Store result
sw r2, 0(r0)         # mem[0] = sum (should be 75)
halt

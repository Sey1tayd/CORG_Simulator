"""
ISA definitions for 16-bit CPU
"""

# Opcodes
OPCODE_R_TYPE = 0x0
OPCODE_ADDI = 0x1
OPCODE_LW = 0x2
OPCODE_SW = 0x3
OPCODE_BEQ = 0x4
OPCODE_J = 0x5
OPCODE_JAL = 0x6
OPCODE_JR = 0x7
OPCODE_BNE = 0x8
OPCODE_HALT = 0x9

# R-type function codes
FUNC_ADD = 0x0
FUNC_SUB = 0x1
FUNC_AND = 0x2
FUNC_OR = 0x3
FUNC_XOR = 0x4
FUNC_SLT = 0x5
FUNC_DIV = 0x6
FUNC_RESERVED = 0x7

# Control signal indices
CTRL_REGDST = 0
CTRL_ALUSRC = 1
CTRL_MEMTOREG = 2
CTRL_REGWRITE = 3
CTRL_MEMREAD = 4
CTRL_MEMWRITE = 5
CTRL_BENCH = 6
CTRL_JUMP = 7

# Control signal values by opcode
CONTROL_SIGNALS = {
    OPCODE_R_TYPE: 0b00001001,  # RegDst=1 (bit0), RegWrite=1 (bit3)
    OPCODE_ADDI:   0b00001010,  # AluSrc=1, RegWrite=1
    OPCODE_LW:     0b00011110,  # AluSrc=1, MemToReg=1, RegWrite=1, MemRead=1
    OPCODE_SW:     0b00100010,  # AluSrc=1, MemWrite=1
    OPCODE_BEQ:    0b01000000,  # Bench=1
    OPCODE_J:      0b10000000,  # Jump=1
    OPCODE_JAL:    0b10001000,  # Jump=1, RegWrite=1
    OPCODE_JR:     0b10000010,  # Jump=1, AluSrc=1
    OPCODE_BNE:    0b01000000,  # Bench=1 (same as BEQ, but branch when NOT zero)
    OPCODE_HALT:   0b00000000,  # No control signals, stops execution
}

def get_control_signals(opcode):
    """Get 8-bit control signals for given opcode"""
    return CONTROL_SIGNALS.get(opcode, 0)

def sign_extend_6(imm6):
    """Sign extend 6-bit immediate to 16-bit"""
    if imm6 & 0x20:  # bit 5 is sign bit
        return imm6 | 0xFFC0
    return imm6 & 0x003F

def sign_extend_16(value):
    """Ensure value is in signed 16-bit range"""
    value = value & 0xFFFF
    if value & 0x8000:
        return value - 0x10000
    return value

def to_unsigned_16(value):
    """Convert to unsigned 16-bit"""
    return value & 0xFFFF

# Instruction mnemonics
R_TYPE_MNEMONICS = {
    FUNC_ADD: "add",
    FUNC_SUB: "sub",
    FUNC_AND: "and",
    FUNC_OR: "or",
    FUNC_XOR: "xor",
    FUNC_SLT: "slt",
    FUNC_DIV: "div",
}

OPCODE_MNEMONICS = {
    OPCODE_ADDI: "addi",
    OPCODE_LW: "lw",
    OPCODE_SW: "sw",
    OPCODE_BEQ: "beq",
    OPCODE_J: "j",
    OPCODE_JAL: "jal",
    OPCODE_JR: "jr",
    OPCODE_BNE: "bne",
    OPCODE_HALT: "halt",
}


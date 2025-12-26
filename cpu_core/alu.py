"""
ALU (Arithmetic Logic Unit) implementation
"""

from .isa import FUNC_ADD, FUNC_SUB, FUNC_AND, FUNC_OR, FUNC_XOR, FUNC_SLT, FUNC_DIV, sign_extend_16, to_unsigned_16


class ALU:
    """16-bit ALU with operations matching ISA"""
    
    @staticmethod
    def execute(a, b, alu_control):
        """
        Execute ALU operation
        Args:
            a, b: 16-bit signed operands
            alu_control: 3-bit control signal (matches func codes)
        Returns:
            (result, zero_flag)
        """
        # Ensure 16-bit signed values
        a = sign_extend_16(a)
        b = sign_extend_16(b)
        
        if alu_control == FUNC_ADD:
            result = a + b
        elif alu_control == FUNC_SUB:
            result = a - b
        elif alu_control == FUNC_AND:
            result = a & b
        elif alu_control == FUNC_OR:
            result = a | b
        elif alu_control == FUNC_XOR:
            result = a ^ b
        elif alu_control == FUNC_SLT:
            result = 1 if a < b else 0
        elif alu_control == FUNC_DIV:
            # DIV-by-zero safe
            if b == 0:
                result = 0
            else:
                result = int(a / b)  # Integer division
        else:
            result = 0
        
        # Truncate to 16-bit
        result = sign_extend_16(result)
        zero = (result == 0)
        
        return to_unsigned_16(result), zero


"""
Disassembler for 16-bit CPU
"""

from .isa import *


class Disassembler:
    """Disassembles machine code to assembly"""
    
    @staticmethod
    def disassemble(instr):
        """Convert 16-bit instruction to assembly string"""
        opcode = (instr >> 12) & 0xF
        rs = (instr >> 9) & 0x7
        rt = (instr >> 6) & 0x7
        rd = (instr >> 3) & 0x7
        func = instr & 0x7
        imm6 = instr & 0x3F
        
        # Sign extend imm6 for display
        if imm6 & 0x20:
            imm_signed = imm6 - 64
        else:
            imm_signed = imm6
        
        # R-type
        if opcode == OPCODE_R_TYPE:
            if func in R_TYPE_MNEMONICS:
                mnemonic = R_TYPE_MNEMONICS[func]
                return f"{mnemonic} r{rd}, r{rs}, r{rt}"
            else:
                # If it's all zeros and not a valid R-type, it's a NOP
                if instr == 0:
                    return "nop"
                return f"unknown_func_{func}"
        
        # I-type
        elif opcode == OPCODE_ADDI:
            return f"addi r{rt}, r{rs}, {imm_signed}"
        
        elif opcode == OPCODE_LW:
            return f"ld r{rt}, {imm_signed}(r{rs})"
        
        elif opcode == OPCODE_SW:
            return f"st r{rt}, {imm_signed}(r{rs})"
        
        elif opcode == OPCODE_BEQ:
            return f"beq r{rs}, r{rt}, {imm_signed}"
        
        elif opcode == OPCODE_BNE:
            return f"bne r{rs}, r{rt}, {imm_signed}"
        
        elif opcode == OPCODE_HALT:
            return "halt"
        
        elif opcode == OPCODE_J:
            # J uses 12-bit unsigned immediate
            imm12 = instr & 0xFFF
            return f"j {imm12}"
        
        elif opcode == OPCODE_JAL:
            # JAL uses 12-bit unsigned immediate
            imm12 = instr & 0xFFF
            return f"jal {imm12}"
        
        elif opcode == OPCODE_JR:
            return f"jr r{rs}"
        
        else:
            return f"unknown_opcode_{opcode}"
    
    @staticmethod
    def disassemble_program(instructions):
        """Disassemble list of instructions"""
        return [
            {
                'pc': i,
                'hex': f"{instr:04X}",
                'asm': Disassembler.disassemble(instr)
            }
            for i, instr in enumerate(instructions)
        ]


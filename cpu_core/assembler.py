"""
Assembler for 16-bit CPU (improved)
- Keeps line mapping (same output length as input)
- Better error reporting
- Correct jump field width (12-bit)
"""

from dataclasses import dataclass
import re
from .isa import *


@dataclass
class AsmError:
    line: int
    message: str
    source: str


@dataclass
class AsmResult:
    words_by_line: list  # same length as input lines; entries are int or None
    errors: list         # list[AsmError]


class Assembler:
    """Assembles assembly code to machine code"""
    
    @staticmethod
    def assemble(assembly_code):
        """
        Assemble text to machine code with label support (two-pass assembly)
        Returns: (instructions, errors)
        - instructions: list with same length as input lines (int or None)
        - errors: list of error strings (for backward compatibility)
        
        Note: instructions list preserves line mapping - None means invalid/blank line
        """
        lines = assembly_code.splitlines()  # do NOT strip() -> preserves final empty line mapping
        words_by_line = []
        errors = []
        error_strings = []  # For backward compatibility
        labels = {}  # label_name -> instruction_address
        
        # PASS 1: Collect labels and their addresses
        instruction_address = 0
        for line_num, original in enumerate(lines, 1):
            # Remove comments
            line = original.split('#')[0].split(';')[0].strip()
            
            if not line:
                continue
            
            # Check for label (ends with ':')
            if ':' in line:
                parts = line.split(':', 1)
                label_name = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""
                
                if label_name:
                    labels[label_name.lower()] = instruction_address
                
                # If there's code after the label, it will be processed in pass 2
                if not rest:
                    continue
                line = rest
            
            # Check if this line will produce an instruction
            if Assembler._is_instruction_line(line):
                instruction_address += 1
        
        # PASS 2: Assemble instructions with label resolution
        instruction_address = 0
        for line_num, original in enumerate(lines, 1):
            # Remove comments
            line = original.split('#')[0].split(';')[0].strip()
            
            if not line:
                # Better default for assembler semantics: ignore -> None (not NOP)
                words_by_line.append(None)
                continue
            
            # Check for label (ends with ':')
            if ':' in line:
                parts = line.split(':', 1)
                rest = parts[1].strip() if len(parts) > 1 else ""
                
                if not rest:
                    # Label only, no instruction
                    words_by_line.append(None)
                    continue
                line = rest
            
            try:
                word = Assembler._assemble_line(line, line_num, original, labels, instruction_address)
                words_by_line.append(word)
                instruction_address += 1
            except Exception as e:
                error_msg = str(e)
                asm_error = AsmError(line=line_num, message=error_msg, source=original.rstrip())
                errors.append(asm_error)
                error_strings.append(f"Line {line_num}: {error_msg}")
                words_by_line.append(None)
        
        # Return tuple for backward compatibility
        # Note: instructions list preserves line mapping (None for errors/blanks)
        return words_by_line, error_strings
    
    @staticmethod
    def _is_instruction_line(line):
        """Check if line contains an instruction (not just a label)"""
        if not line:
            return False
        # Remove label if present
        if ':' in line:
            parts = line.split(':', 1)
            rest = parts[1].strip() if len(parts) > 1 else ""
            if not rest:
                return False
            line = rest
        # Check if it starts with a valid mnemonic
        parts = line.split(None, 1)
        if not parts:
            return False
        mnemonic = parts[0].lower()
        valid_mnemonics = ['add', 'sub', 'and', 'or', 'xor', 'slt', 'div', 'addi', 'lw', 'ld', 'sw', 'st', 
                          'beq', 'bne', 'j', 'jal', 'jr', 'nop', 'halt']
        return mnemonic in valid_mnemonics
    
    @staticmethod
    def _assemble_line(line, line_num, original_line, labels=None, current_pc=0):
        """Assemble single instruction with optional label resolution"""
        if labels is None:
            labels = {}
        
        if not line:
            return 0
        
        # Normalize whitespace but preserve structure
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Extract mnemonic
        parts = line.split(None, 1)  # Split only on first whitespace
        if not parts:
            raise ValueError("Empty instruction")
        
        mnemonic = parts[0].lower()
        operands_str = parts[1] if len(parts) > 1 else ""
        
        # Handle aliases
        if mnemonic == 'ld':
            mnemonic = 'lw'
        elif mnemonic == 'st':
            mnemonic = 'sw'
        
        # R-type instructions: add rd, rs, rt
        r_type_ops = {'add': FUNC_ADD, 'sub': FUNC_SUB, 'and': FUNC_AND,
                      'or': FUNC_OR, 'xor': FUNC_XOR, 'slt': FUNC_SLT, 'div': FUNC_DIV}
        
        if mnemonic in r_type_ops:
            operands = Assembler._parse_operands(operands_str, 3, f"{mnemonic} rd, rs, rt")
            rd = Assembler._parse_reg(operands[0], line_num, original_line)
            rs = Assembler._parse_reg(operands[1], line_num, original_line)
            rt = Assembler._parse_reg(operands[2], line_num, original_line)
            func = r_type_ops[mnemonic]
            return (OPCODE_R_TYPE << 12) | (rs << 9) | (rt << 6) | (rd << 3) | func
        
        # ADDI: addi rt, rs, imm
        elif mnemonic == 'addi':
            operands = Assembler._parse_operands(operands_str, 3, "addi rt, rs, imm6")
            rt = Assembler._parse_reg(operands[0], line_num, original_line)
            rs = Assembler._parse_reg(operands[1], line_num, original_line)
            imm6 = Assembler._parse_imm_signed(operands[2], bits=6)  # -32..31
            return (OPCODE_ADDI << 12) | (rs << 9) | (rt << 6) | (imm6 & 0x3F)
        
        # LW: lw rt, imm(rs)
        elif mnemonic == 'lw':
            operands = Assembler._parse_operands(operands_str, 2, "lw rt, imm6(rs)", allow_parentheses=True)
            rt = Assembler._parse_reg(operands[0], line_num, original_line)
            # Parse imm(rs) format
            imm6, rs = Assembler._parse_mem_operand(operands[1], line_num, original_line)
            return (OPCODE_LW << 12) | (rs << 9) | (rt << 6) | (imm6 & 0x3F)
        
        # SW: sw rt, imm(rs)
        elif mnemonic == 'sw':
            operands = Assembler._parse_operands(operands_str, 2, "sw rt, imm6(rs)", allow_parentheses=True)
            rt = Assembler._parse_reg(operands[0], line_num, original_line)
            # Parse imm(rs) format
            imm6, rs = Assembler._parse_mem_operand(operands[1], line_num, original_line)
            return (OPCODE_SW << 12) | (rs << 9) | (rt << 6) | (imm6 & 0x3F)
        
        # BEQ: beq rs, rt, imm
        elif mnemonic == 'beq':
            operands = Assembler._parse_operands(operands_str, 3, "beq rs, rt, off6")
            rs = Assembler._parse_reg(operands[0], line_num, original_line)
            rt = Assembler._parse_reg(operands[1], line_num, original_line)
            off6 = Assembler._parse_branch_operand(operands[2], labels, current_pc, line_num, original_line)
            return (OPCODE_BEQ << 12) | (rs << 9) | (rt << 6) | (off6 & 0x3F)
        
        # BNE: bne rs, rt, imm
        elif mnemonic == 'bne':
            operands = Assembler._parse_operands(operands_str, 3, "bne rs, rt, off6")
            rs = Assembler._parse_reg(operands[0], line_num, original_line)
            rt = Assembler._parse_reg(operands[1], line_num, original_line)
            off6 = Assembler._parse_branch_operand(operands[2], labels, current_pc, line_num, original_line)
            return (OPCODE_BNE << 12) | (rs << 9) | (rt << 6) | (off6 & 0x3F)
        
        # HALT: halt
        elif mnemonic == 'halt':
            if operands_str:
                raise ValueError(f"halt takes no operands, got: {operands_str}")
            return (OPCODE_HALT << 12)
        
        # Jump uses 12-bit absolute address
        elif mnemonic == 'j':
            operands = Assembler._parse_operands(operands_str, 1, "j target")
            imm12 = Assembler._parse_jump_operand(operands[0], labels, current_pc, line_num, original_line)
            return (OPCODE_J << 12) | (imm12 & 0xFFF)
        
        elif mnemonic == 'jal':
            operands = Assembler._parse_operands(operands_str, 1, "jal target")
            imm12 = Assembler._parse_jump_operand(operands[0], labels, current_pc, line_num, original_line)
            return (OPCODE_JAL << 12) | (imm12 & 0xFFF)
        
        # JR: jr rs
        elif mnemonic == 'jr':
            operands = Assembler._parse_operands(operands_str, 1, "jr rs")
            rs = Assembler._parse_reg(operands[0], line_num, original_line)
            return (OPCODE_JR << 12) | (rs << 9)
        
        # NOP
        elif mnemonic == 'nop':
            if operands_str:
                raise ValueError(f"nop takes no operands, got: {operands_str}")
            return 0
        
        else:
            raise ValueError(f"Unknown instruction: '{mnemonic}'. Valid instructions: add, sub, and, or, xor, slt, div, addi, lw, ld, sw, st, beq, bne, j, jal, jr, nop, halt")
    
    @staticmethod
    def _parse_operands(operands_str, expected_count, format_str, allow_parentheses=False):
        """Parse comma-separated operands"""
        if not operands_str:
            if expected_count > 0:
                raise ValueError(f"Expected {expected_count} operand(s), got none. Format: {format_str}")
            return []
        
        # Split by comma, but preserve parentheses content
        if allow_parentheses:
            # For lw/sw, we need to handle imm(rs) specially
            # Split on comma, but don't split inside parentheses
            parts = []
            current = ""
            paren_depth = 0
            for char in operands_str:
                if char == '(':
                    paren_depth += 1
                    current += char
                elif char == ')':
                    paren_depth -= 1
                    current += char
                elif char == ',' and paren_depth == 0:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
            if current.strip():
                parts.append(current.strip())
        else:
            parts = [p.strip() for p in operands_str.split(',')]
        
        # Filter empty parts
        parts = [p for p in parts if p]
        
        if len(parts) != expected_count:
            raise ValueError(f"Expected {expected_count} operand(s), got {len(parts)}. Format: {format_str}")
        
        return parts
    
    @staticmethod
    def _parse_mem_operand(mem_str, line_num, original_line):
        """Parse memory operand in format imm(rs)"""
        mem_str = mem_str.strip()
        
        # Check for parentheses
        if '(' not in mem_str or ')' not in mem_str:
            raise ValueError(f"Memory operand must be in format imm(rs), got: '{mem_str}'")
        
        # Extract parts
        paren_idx = mem_str.index('(')
        imm_str = mem_str[:paren_idx].strip()
        rs_str = mem_str[paren_idx+1:].rstrip(')').strip()
        
        if not imm_str:
            raise ValueError(f"Missing immediate value in memory operand: '{mem_str}'")
        if not rs_str:
            raise ValueError(f"Missing register in memory operand: '{mem_str}'")
        
        imm = Assembler._parse_imm_signed(imm_str, bits=6)  # Memory offsets use 6-bit signed
        rs = Assembler._parse_reg(rs_str, line_num, original_line)
        
        return imm, rs
    
    @staticmethod
    def _parse_reg(reg_str, line_num, original_line):
        """Parse register string (r0-r7)"""
        if not reg_str:
            raise ValueError(f"Empty register string")
        
        reg_str = reg_str.lower().strip()
        
        if not reg_str.startswith('r'):
            raise ValueError(f"Invalid register format: '{reg_str}'. Expected r0-r7")
        
        try:
            reg_num = int(reg_str[1:])
        except ValueError:
            raise ValueError(f"Invalid register number: '{reg_str}'. Expected r0-r7")
        
        if reg_num < 0 or reg_num > 7:
            raise ValueError(f"Register out of range: '{reg_str}'. Valid registers: r0-r7")
        
        return reg_num
    
    @staticmethod
    def _parse_int(s):
        """Parse integer from string (supports hex, binary, decimal)"""
        s = s.strip().lower()
        if s.startswith("-0x"):
            return -int(s[3:], 16)
        if s.startswith("0x"):
            return int(s[2:], 16)
        if s.startswith("0b"):
            return int(s[2:], 2)
        if s.startswith("-0b"):
            return -int(s[3:], 2)
        return int(s, 10)
    
    @staticmethod
    def _parse_imm_signed(s, bits):
        """Parse signed immediate value with specified bit width"""
        val = Assembler._parse_int(s)
        lo = -(1 << (bits - 1))
        hi = (1 << (bits - 1)) - 1
        if val < lo or val > hi:
            raise ValueError(f"Immediate out of range [{lo}, {hi}]: {val} (from '{s}')")
        return val & ((1 << bits) - 1)  # two's complement form
    
    @staticmethod
    def _parse_imm_unsigned(s, bits):
        """Parse unsigned immediate value with specified bit width"""
        val = Assembler._parse_int(s)
        lo = 0
        hi = (1 << bits) - 1
        if val < lo or val > hi:
            raise ValueError(f"Immediate out of range [{lo}, {hi}]: {val} (from '{s}')")
        return val
    
    @staticmethod
    def _parse_imm(imm_str, line_num, original_line):
        """Parse immediate value (backward compatibility - uses 6-bit signed)"""
        # This method kept for backward compatibility but delegates to _parse_imm_signed
        return Assembler._parse_imm_signed(imm_str, bits=6)
    
    @staticmethod
    def _parse_branch_operand(operand_str, labels, current_pc, line_num, original_line):
        """Parse branch operand (can be immediate or label)"""
        operand_str = operand_str.strip()
        
        # Check if it looks like a label (alphabetic, not starting with digit or 0x/0b)
        is_likely_label = operand_str and operand_str[0].isalpha() and not operand_str.lower().startswith(('0x', '0b', '-0x', '-0b'))
        
        if is_likely_label:
            if operand_str.lower() in labels:
                target_pc = labels[operand_str.lower()]
                offset = target_pc - (current_pc + 1)  # Branch offset is relative to next instruction
                if offset < -32 or offset > 31:
                    raise ValueError(f"Branch offset out of range [-32, 31]: {offset} (from label '{operand_str}')")
                return offset & 0x3F
            else:
                raise ValueError(f"Undefined label: '{operand_str}'")
        
        # Otherwise parse as immediate
        return Assembler._parse_imm_signed(operand_str, bits=6)
    
    @staticmethod
    def _parse_jump_operand(operand_str, labels, current_pc, line_num, original_line):
        """Parse jump operand (can be immediate or label) - returns PC-relative offset"""
        operand_str = operand_str.strip()
        
        # Check if it looks like a label (alphabetic, not starting with digit or 0x/0b)
        is_likely_label = operand_str and operand_str[0].isalpha() and not operand_str.lower().startswith(('0x', '0b', '-0x', '-0b'))
        
        if is_likely_label:
            if operand_str.lower() in labels:
                target_pc = labels[operand_str.lower()]
                # Calculate PC-relative offset (relative to current instruction's PC)
                offset = target_pc - current_pc
                if offset < -2048 or offset > 2047:
                    raise ValueError(f"Jump offset out of range [-2048, 2047]: {offset} (from label '{operand_str}')")
                return offset & 0xFFF  # Return as 12-bit two's complement
            else:
                raise ValueError(f"Undefined label: '{operand_str}'")
        
        # Otherwise parse as signed immediate (PC-relative offset)
        return Assembler._parse_imm_signed(operand_str, bits=12)


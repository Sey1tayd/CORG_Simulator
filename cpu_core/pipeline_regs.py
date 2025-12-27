"""
Pipeline register definitions
"""


class IF_ID:
    """IF/ID pipeline register"""
    def __init__(self):
        self.pc_plus_1 = 0
        self.instr = 0
        
    def reset(self):
        self.pc_plus_1 = 0
        self.instr = 0
    
    def write(self, pc_plus_1, instr):
        self.pc_plus_1 = pc_plus_1
        self.instr = instr
    
    def to_dict(self):
        return {
            'pc_plus_1': self.pc_plus_1,
            'instr': self.instr,
            'instr_hex': f"{self.instr:04X}"
        }


class ID_EX:
    """ID/EX pipeline register"""
    def __init__(self):
        self.pc = 0
        self.instr = 0
        self.read_data1 = 0
        self.read_data2 = 0
        self.imm = 0
        self.rs = 0
        self.rt = 0
        self.dest_reg = 0
        self.ctrl = 0
        self.alu_ctrl = 0
        
    def reset(self):
        self.pc = 0
        self.instr = 0
        self.read_data1 = 0
        self.read_data2 = 0
        self.imm = 0
        self.rs = 0
        self.rt = 0
        self.dest_reg = 0
        self.ctrl = 0
        self.alu_ctrl = 0
    
    def write(self, pc, instr, rd1, rd2, imm, rs, rt, dest_reg, ctrl, alu_ctrl):
        self.pc = pc
        self.instr = instr
        self.read_data1 = rd1
        self.read_data2 = rd2
        self.imm = imm
        self.rs = rs
        self.rt = rt
        self.dest_reg = dest_reg
        self.ctrl = ctrl
        self.alu_ctrl = alu_ctrl
    
    def flush(self):
        """Clear control signals (bubble/NOP)"""
        self.ctrl = 0
    
    def to_dict(self):
        return {
            'pc': self.pc,
            'instr': self.instr,
            'instr_hex': f"{self.instr:04X}",
            'read_data1': self.read_data1,
            'read_data2': self.read_data2,
            'imm': self.imm,
            'rs': self.rs,
            'rt': self.rt,
            'dest_reg': self.dest_reg,
            'ctrl': f"{self.ctrl:08b}",
            'alu_ctrl': self.alu_ctrl
        }


class EX_MEM:
    """EX/MEM pipeline register"""
    def __init__(self):
        self.pc = 0
        self.instr = 0
        self.branch_target = 0
        self.zero = False
        self.alu_result = 0
        self.read_data2 = 0  # For store
        self.dest_reg = 0
        self.ctrl = 0
        
    def reset(self):
        self.pc = 0
        self.instr = 0
        self.branch_target = 0
        self.zero = False
        self.alu_result = 0
        self.read_data2 = 0
        self.dest_reg = 0
        self.ctrl = 0

    def write(self, pc, instr, branch_target, zero, alu_result, rd2, dest_reg, ctrl):
        self.pc = pc
        self.instr = instr
        self.branch_target = branch_target
        self.zero = zero
        self.alu_result = alu_result
        self.read_data2 = rd2
        self.dest_reg = dest_reg
        self.ctrl = ctrl

    def to_dict(self):
        return {
            'pc': self.pc,
            'instr': self.instr,
            'instr_hex': f"{self.instr:04X}",
            'branch_target': self.branch_target,
            'zero': self.zero,
            'alu_result': self.alu_result,
            'read_data2': self.read_data2,
            'dest_reg': self.dest_reg,
            'ctrl': f"{self.ctrl:08b}"
        }


class MEM_WB:
    """MEM/WB pipeline register"""
    def __init__(self):
        self.pc = 0
        self.instr = 0
        self.mem_data = 0
        self.alu_result = 0
        self.dest_reg = 0
        self.ctrl = 0
        
    def reset(self):
        self.pc = 0
        self.instr = 0
        self.mem_data = 0
        self.alu_result = 0
        self.dest_reg = 0
        self.ctrl = 0

    def write(self, pc, instr, mem_data, alu_result, dest_reg, ctrl):
        self.pc = pc
        self.instr = instr
        self.mem_data = mem_data
        self.alu_result = alu_result
        self.dest_reg = dest_reg
        self.ctrl = ctrl

    def to_dict(self):
        return {
            'pc': self.pc,
            'instr': self.instr,
            'instr_hex': f"{self.instr:04X}",
            'mem_data': self.mem_data,
            'alu_result': self.alu_result,
            'dest_reg': self.dest_reg,
            'ctrl': f"{self.ctrl:08b}"
        }

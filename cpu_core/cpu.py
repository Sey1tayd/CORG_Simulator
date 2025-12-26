"""
Main CPU class - 5-stage pipelined processor
"""

from .isa import *
from .alu import ALU
from .hazard import ForwardingUnit, HazardDetectionUnit
from .disassembler import Disassembler
from .pipeline_regs import IF_ID, ID_EX, EX_MEM, MEM_WB


class CPU:
    """5-stage pipelined 16-bit CPU"""
    
    def __init__(self):
        # Program counter
        self.pc = 0
        
        # Register file (8 registers, 16-bit each)
        self.regs = [0] * 8
        
        # Memory
        self.instr_mem = [0] * 256  # 256 instructions
        self.data_mem = [0] * 256   # 256 words of data memory
        
        # Pipeline registers
        self.if_id = IF_ID()
        self.id_ex = ID_EX()
        self.ex_mem = EX_MEM()
        self.mem_wb = MEM_WB()
        
        # Cycle counter
        self.cycle = 0
        
        # Execution state
        self.running = False
        self.breakpoints = set()
        
        # Hazard signals (for display)
        self.hazard_info = {
            'stall': False,
            'flush_ifid': False,
            'flush_idex': False,
            'forward_a': "00",
            'forward_b': "00",
            'store_fwd': False,
            'pc_src': False
        }
        
        # Stage info for display
        self.stage_info = {
            'if': {},
            'id': {},
            'ex': {},
            'mem': {},
            'wb': {}
        }
    
    def reset(self):
        """Reset CPU state"""
        self.pc = 0
        self.regs = [0] * 8
        self.data_mem = [0] * 256
        self.instr_mem = [0] * 256  # Clear instruction memory
        self.if_id.reset()
        self.id_ex.reset()
        self.ex_mem.reset()
        self.mem_wb.reset()
        self.cycle = 0
        self.running = False
        self.hazard_info = {
            'stall': False,
            'flush_ifid': False,
            'flush_idex': False,
            'forward_a': "00",
            'forward_b': "00",
            'store_fwd': False,
            'pc_src': False
        }
    
    def load_program(self, instructions):
        """Load program into instruction memory"""
        # Filter out None values (blank lines, errors) - assembler preserves line mapping
        valid_instructions = [instr for instr in instructions if instr is not None]
        for i, instr in enumerate(valid_instructions):
            if i < 256:
                self.instr_mem[i] = instr & 0xFFFF
    
    def step(self):
        """Execute one clock cycle"""
        # Check for HALT instruction in IF stage
        if self.pc < 256:
            instr = self.instr_mem[self.pc]
            opcode = (instr >> 12) & 0xF
            if opcode == OPCODE_HALT:
                self.running = False
                return  # Stop execution
        
        # Execute stages in reverse order (WB -> IF) to simulate parallel execution
        self._wb_stage()
        self._mem_stage()
        self._ex_stage()
        self._id_stage()
        self._if_stage()
        
        # Update cycle counter
        self.cycle += 1
        
        # Keep r0 as 0
        self.regs[0] = 0
    
    def _if_stage(self):
        """IF: Instruction Fetch"""
        # Check hazard detection
        if_id_rs = (self.if_id.instr >> 9) & 0x7
        if_id_rt = (self.if_id.instr >> 6) & 0x7
        id_ex_memread = (self.id_ex.ctrl >> CTRL_MEMREAD) & 1
        
        pc_write, if_id_write, id_ex_flush = HazardDetectionUnit.detect(
            id_ex_memread, self.id_ex.rt, if_id_rs, if_id_rt
        )
        
        # Fetch instruction
        instr = self.instr_mem[self.pc] if 0 <= self.pc < 256 else 0
        pc_plus_1 = self.pc + 1
        
        # Update IF/ID register if not stalled
        if if_id_write:
            # Check for flush (branch/jump taken)
            if self.hazard_info['pc_src']:
                self.if_id.write(pc_plus_1, 0)  # NOP
                self.hazard_info['flush_ifid'] = True
            else:
                self.if_id.write(pc_plus_1, instr)
                self.hazard_info['flush_ifid'] = False
        
        # Update PC if not stalled
        if pc_write and not self.hazard_info['pc_src']:
            self.pc = pc_plus_1
        
        self.hazard_info['stall'] = not pc_write
        self.hazard_info['flush_idex'] = id_ex_flush
        
        # Stage info
        self.stage_info['if'] = {
            'pc': self.pc,
            'instr': instr,
            'instr_hex': f"{instr:04X}",
            'pc_plus_1': pc_plus_1,
            'asm': Disassembler.disassemble(instr) if instr != 0 else 'nop'
        }
    
    def _id_stage(self):
        """ID: Instruction Decode"""
        instr = self.if_id.instr
        
        # Decode instruction
        opcode = (instr >> 12) & 0xF
        rs = (instr >> 9) & 0x7
        rt = (instr >> 6) & 0x7
        rd = (instr >> 3) & 0x7
        func = instr & 0x7
        imm6 = instr & 0x3F
        imm12 = instr & 0xFFF  # For J/JAL
        
        # Control signals
        ctrl = get_control_signals(opcode)
        
        # ALU control
        if opcode == OPCODE_R_TYPE:
            alu_ctrl = func
        elif opcode == OPCODE_BEQ or opcode == OPCODE_BNE:
            alu_ctrl = FUNC_SUB  # For comparison (set Zero flag)
        else:
            alu_ctrl = FUNC_ADD  # For ADDI, LW, SW
        
        # Read registers with bypass
        read_data1 = self._read_register_with_bypass(rs)
        read_data2 = self._read_register_with_bypass(rt)
        
        # Sign extend immediate (6-bit for most instructions, 12-bit for J/JAL)
        if opcode == OPCODE_J or opcode == OPCODE_JAL:
            # Sign extend 12-bit immediate for PC-relative addressing
            if imm12 & 0x800:  # bit 11 is sign bit
                imm_extended = imm12 | 0xF000  # Sign extend to 16-bit
            else:
                imm_extended = imm12
        else:
            imm_extended = sign_extend_6(imm6)
        
        # Destination register
        reg_dst = (ctrl >> CTRL_REGDST) & 1
        jump = (ctrl >> CTRL_JUMP) & 1
        reg_write = (ctrl >> CTRL_REGWRITE) & 1
        
        # JAL: force destination to r7
        is_jal = jump and reg_write
        if is_jal:
            dest_reg = 7
        elif reg_dst:
            dest_reg = rd
        else:
            dest_reg = rt
        
        # Check for hazard flush
        if self.hazard_info['flush_idex'] or self.hazard_info['pc_src']:
            ctrl = 0  # Insert bubble
        
        # Write to ID/EX
        self.id_ex.write(
            self.if_id.pc_plus_1 - 1,  # PC of this instruction
            instr,  # Instruction for display
            read_data1,
            read_data2,
            imm_extended,
            rs,
            rt,
            dest_reg,
            ctrl,
            alu_ctrl
        )
        
        # Stage info
        self.stage_info['id'] = {
            'instr': instr,
            'instr_hex': f"{instr:04X}",
            'opcode': opcode,
            'rs': rs,
            'rt': rt,
            'rd': rd,
            'func': func,
            'imm6': imm6,
            'ctrl': f"{ctrl:08b}",
            'read_data1': read_data1,
            'read_data2': read_data2,
            'asm': Disassembler.disassemble(instr) if instr != 0 else 'nop'
        }
    
    def _ex_stage(self):
        """EX: Execute"""
        # Get control signals
        ctrl = self.id_ex.ctrl
        alu_src = (ctrl >> CTRL_ALUSRC) & 1
        jump = (ctrl >> CTRL_JUMP) & 1
        bench = (ctrl >> CTRL_BENCH) & 1
        reg_write_ex = (ctrl >> CTRL_REGWRITE) & 1
        
        # Forwarding
        forward_a, forward_b = ForwardingUnit.compute(
            self.id_ex.rs,
            self.id_ex.rt,
            (self.ex_mem.ctrl >> CTRL_REGWRITE) & 1,
            self.ex_mem.dest_reg,
            (self.mem_wb.ctrl >> CTRL_REGWRITE) & 1,
            self.mem_wb.dest_reg
        )
        
        self.hazard_info['forward_a'] = forward_a
        self.hazard_info['forward_b'] = forward_b
        
        # ALU operand A (with forwarding)
        if forward_a == "10":
            alu_a = self.ex_mem.alu_result
        elif forward_a == "01":
            alu_a = self._get_wb_write_data()
        else:
            alu_a = self.id_ex.read_data1
        
        # ALU operand B (with forwarding for register, then AluSrc mux)
        if forward_b == "10":
            reg_b = self.ex_mem.alu_result
        elif forward_b == "01":
            reg_b = self._get_wb_write_data()
        else:
            reg_b = self.id_ex.read_data2
        
        # AluSrc mux
        alu_b = self.id_ex.imm if alu_src else reg_b
        
        # Execute ALU
        alu_result, zero = ALU.execute(alu_a, alu_b, self.id_ex.alu_ctrl)
        
        # Branch target
        branch_target = self.id_ex.pc + self.id_ex.imm
        
        # JAL: ALU result = return address
        is_jal = jump and reg_write_ex
        if is_jal:
            alu_result = self.id_ex.pc + 1
        
        # Check if this is BNE instruction (opcode in instruction)
        instr = self.id_ex.instr
        opcode = (instr >> 12) & 0xF
        is_bne = (opcode == OPCODE_BNE)
        
        # PC control
        # BEQ: branch when zero, BNE: branch when NOT zero
        if is_bne:
            branch_taken = bench and not zero
        else:
            branch_taken = bench and zero
        pc_src = branch_taken or jump
        self.hazard_info['pc_src'] = pc_src
        
        # Update PC for branch/jump
        if pc_src:
            # JR: use register value (ReadData1)
            is_jr = jump and alu_src
            if is_jr:
                self.pc = alu_a & 0xFFFF
            else:
                # J/JAL/Branch: PC-relative (PC + imm)
                self.pc = branch_target & 0xFFFF
        
        # Store data forwarding
        store_data = reg_b  # Already forwarded
        
        # Get instruction from ID/EX pipeline register
        ex_pc = self.id_ex.pc
        ex_instr = self.id_ex.instr  # Use instruction stored in ID/EX register
        
        # Write to EX/MEM
        self.ex_mem.write(
            ex_instr,  # Instruction for display
            branch_target,
            zero,
            alu_result,
            store_data,
            self.id_ex.dest_reg,
            ctrl
        )
        
        # Stage info
        self.stage_info['ex'] = {
            'pc': ex_pc,
            'instr': ex_instr,
            'instr_hex': f"{ex_instr:04X}",
            'asm': Disassembler.disassemble(ex_instr) if ex_instr != 0 else 'nop',
            'alu_a': alu_a,
            'alu_b': alu_b,
            'alu_ctrl': self.id_ex.alu_ctrl,
            'alu_result': alu_result,
            'zero': zero,
            'branch_target': branch_target,
            'pc_src': pc_src,
            'forward_a': forward_a,
            'forward_b': forward_b
        }
    
    def _mem_stage(self):
        """MEM: Memory Access"""
        ctrl = self.ex_mem.ctrl
        mem_read = (ctrl >> CTRL_MEMREAD) & 1
        mem_write = (ctrl >> CTRL_MEMWRITE) & 1
        
        mem_data = 0
        
        # Memory access
        addr = self.ex_mem.alu_result & 0xFF  # 8-bit address
        
        if mem_read:
            mem_data = self.data_mem[addr]
        
        if mem_write:
            self.data_mem[addr] = self.ex_mem.read_data2 & 0xFFFF
        
        # Get instruction from EX/MEM pipeline register
        mem_instr = self.ex_mem.instr  # Use instruction stored in EX/MEM register
        
        # Write to MEM/WB
        self.mem_wb.write(
            mem_instr,  # Instruction for display
            mem_data,
            self.ex_mem.alu_result,
            self.ex_mem.dest_reg,
            ctrl
        )
        
        # Stage info
        self.stage_info['mem'] = {
            'pc': 0,  # PC not needed for display, instruction is stored
            'instr': mem_instr,
            'instr_hex': f"{mem_instr:04X}",
            'asm': Disassembler.disassemble(mem_instr) if mem_instr != 0 else 'nop',
            'addr': addr,
            'mem_read': mem_read,
            'mem_write': mem_write,
            'mem_data': mem_data,
            'write_data': self.ex_mem.read_data2 if mem_write else 0
        }
    
    def _wb_stage(self):
        """WB: Write Back"""
        ctrl = self.mem_wb.ctrl
        reg_write = (ctrl >> CTRL_REGWRITE) & 1
        mem_to_reg = (ctrl >> CTRL_MEMTOREG) & 1
        
        # Write back data selection
        write_data = self._get_wb_write_data()
        
        # Write to register file
        if reg_write and self.mem_wb.dest_reg != 0:
            self.regs[self.mem_wb.dest_reg] = write_data & 0xFFFF
        
        # Get instruction from MEM/WB pipeline register
        wb_instr = self.mem_wb.instr  # Use instruction stored in MEM/WB register
        
        # Stage info
        self.stage_info['wb'] = {
            'pc': 0,  # PC not needed for display, instruction is stored
            'instr': wb_instr,
            'instr_hex': f"{wb_instr:04X}",
            'asm': Disassembler.disassemble(wb_instr) if wb_instr != 0 else 'nop',
            'dest_reg': self.mem_wb.dest_reg,
            'write_data': write_data,
            'reg_write': reg_write
        }
    
    def _get_wb_write_data(self):
        """Get write-back data (MemToReg mux)"""
        ctrl = self.mem_wb.ctrl
        mem_to_reg = (ctrl >> CTRL_MEMTOREG) & 1
        return self.mem_wb.mem_data if mem_to_reg else self.mem_wb.alu_result
    
    def _read_register_with_bypass(self, reg):
        """Read register with write-first bypass from WB stage"""
        # Check if WB is writing to this register
        ctrl = self.mem_wb.ctrl
        reg_write = (ctrl >> CTRL_REGWRITE) & 1
        
        if reg_write and self.mem_wb.dest_reg == reg and reg != 0:
            return self._get_wb_write_data()
        
        return self.regs[reg]
    
    def get_state(self):
        """Get complete CPU state for UI"""
        return {
            'cycle': self.cycle,
            'pc': self.pc,
            'pipeline_regs': {
                'if_id': self.if_id.to_dict(),
                'id_ex': self.id_ex.to_dict(),
                'ex_mem': self.ex_mem.to_dict(),
                'mem_wb': self.mem_wb.to_dict()
            },
            'hazards': self.hazard_info.copy(),
            'stage_info': self.stage_info.copy(),
            'regfile': [{'r': i, 'v': self.regs[i]} for i in range(8)],
            'data_mem': [{'addr': i, 'v': self.data_mem[i]} for i in range(256) if self.data_mem[i] != 0],
        }


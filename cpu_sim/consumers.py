"""
WebSocket consumer for CPU simulation
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from cpu_core import CPU, Assembler, Disassembler


class CPUConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for CPU control"""
    
    cpu_instances = {}  # Store CPU instances per connection
    
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        
        # Create CPU instance for this connection
        self.cpu = CPU()
        self.running = False
        self.run_task = None
        self.run_hz = 10
        
        # Send initial state
        await self.send_state()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.run_task:
            self.run_task.cancel()
    
    async def receive(self, text_data):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(text_data)
            cmd = data.get('cmd')
            
            if cmd == 'reset':
                await self.handle_reset()
            elif cmd == 'step':
                await self.handle_step()
            elif cmd == 'run':
                await self.handle_run(data)
            elif cmd == 'pause':
                await self.handle_pause()
            elif cmd == 'load_program':
                await self.handle_load_program(data)
            elif cmd == 'compile':
                await self.handle_compile(data)
            elif cmd == 'set_breakpoints':
                await self.handle_set_breakpoints(data)
            elif cmd == 'set_memory':
                await self.handle_set_memory(data)
            elif cmd == 'set_register':
                await self.handle_set_register(data)
            else:
                await self.send_error(f"Unknown command: {cmd}")
        
        except Exception as e:
            await self.send_error(str(e))
    
    async def handle_reset(self):
        """Reset CPU"""
        if self.run_task:
            self.run_task.cancel()
            self.running = False
        
        self.cpu.reset()
        await self.send_state()
    
    async def handle_step(self):
        """Execute one cycle"""
        if self.running:
            return
        
        self.cpu.step()
        await self.send_state()
    
    async def handle_run(self, data):
        """Start continuous execution"""
        if self.running:
            return
        
        self.run_hz = data.get('hz', 10)
        self.running = True
        
        # Start run loop
        self.run_task = asyncio.create_task(self.run_loop())
    
    async def handle_pause(self):
        """Pause execution"""
        if self.run_task:
            self.run_task.cancel()
        self.running = False
        await self.send_state()
    
    async def handle_compile(self, data):
        """Compile assembly code and return machine code (without loading into CPU)"""
        if 'assembly' not in data:
            await self.send_error("No assembly code provided")
            return
            
        assembly = data['assembly']
        instructions, errors = Assembler.assemble(assembly)
        
        # Convert to machine code format - preserve line mapping
        machine_code = []
        error_lines = {error.line for error in errors if hasattr(error, 'line')}
        
        for i, instr in enumerate(instructions):
            line_num = i + 1
            if instr is not None:
                asm = Disassembler.disassemble(instr)
                machine_code.append({
                    'line': line_num,
                    'pc': len(machine_code),  # PC for loaded program
                    'hex': f'{instr:04X}',
                    'binary': f'{instr:016b}',
                    'value': instr,
                    'asm': asm
                })
            else:
                # Check if this is a blank line or an error
                is_error = line_num in error_lines
                machine_code.append({
                    'line': line_num,
                    'error': is_error,  # Only True if it's a real error
                    'blank': not is_error,  # True if it's just a blank line
                    'hex': '0000',
                    'binary': '0000000000000000',
                    'value': None,
                    'asm': '----'
                })
        
        # Convert AsmError objects to dicts for JSON serialization
        error_dicts = []
        for error in errors:
            if hasattr(error, 'line'):
                error_dicts.append({
                    'line': error.line,
                    'message': error.message,
                    'source': error.source
                })
            else:
                # Backward compatibility for string errors
                error_dicts.append({
                    'line': 0,
                    'message': str(error),
                    'source': ''
                })
        
        await self.send(text_data=json.dumps({
            'type': 'compile_result',
            'machine_code': machine_code,
            'errors': error_dicts,
            'has_errors': len(error_dicts) > 0
        }))
    
    async def handle_load_program(self, data):
        """Load program into instruction memory"""
        if 'assembly' not in data:
            await self.send_error("No assembly code provided")
            return
            
        assembly = data['assembly']
        instructions, errors = Assembler.assemble(assembly)
        
        if errors:
            # Convert AsmError objects to dicts for JSON serialization
            error_dicts = []
            for error in errors:
                if hasattr(error, 'line'):
                    error_dicts.append({
                        'line': error.line,
                        'message': error.message,
                        'source': error.source
                    })
                else:
                    # Backward compatibility for string errors
                    error_dicts.append({
                        'line': 0,
                        'message': str(error),
                        'source': ''
                    })
            
            await self.send(text_data=json.dumps({
                'type': 'error',
                'errors': error_dicts,
                'message': f'Assembly failed: {len(error_dicts)} error(s)'
            }))
            return
        
        valid_instructions = [instr for instr in instructions if instr is not None]
        
        if not valid_instructions:
            await self.send_error("No valid instructions to load")
            return
        
        self.cpu.reset()
        self.cpu.load_program(valid_instructions)
        await self.send_state()
    
    async def handle_set_breakpoints(self, data):
        """Set breakpoints"""
        pcs = data.get('pcs', [])
        self.cpu.breakpoints = set(pcs)
    
    async def handle_set_memory(self, data):
        """Set memory value"""
        addr = data.get('addr', 0)
        value = data.get('value', 0)
        if 0 <= addr < 256:
            self.cpu.data_mem[addr] = value & 0xFFFF
        await self.send_state()
    
    async def handle_set_register(self, data):
        """Set register value"""
        reg = data.get('reg', 0)
        value = data.get('value', 0)
        if 0 <= reg <= 7:
            self.cpu.regs[reg] = value & 0xFFFF
        await self.send_state()
    
    async def run_loop(self):
        """Continuous execution loop"""
        try:
            while self.running:
                # Check breakpoint
                if self.cpu.pc in self.cpu.breakpoints:
                    self.running = False
                    await self.send_state()
                    break
                
                # Execute one cycle
                self.cpu.step()
                
                # Send state update
                await self.send_state()
                
                # Delay based on Hz
                await asyncio.sleep(1.0 / self.run_hz)
        
        except asyncio.CancelledError:
            pass
    
    async def send_state(self):
        """Send CPU state to client"""
        state = self.cpu.get_state()
        
        # Add instruction memory with disassembly
        instr_mem = Disassembler.disassemble_program(self.cpu.instr_mem)
        state['instr_mem'] = instr_mem
        
        await self.send(text_data=json.dumps({
            'type': 'state',
            **state
        }))
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))


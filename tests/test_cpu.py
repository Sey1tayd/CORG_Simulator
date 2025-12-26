"""
Unit tests for CPU core
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cpu_core import CPU, Assembler


def test_basic_execution():
    """Test basic instruction execution"""
    cpu = CPU()
    
    # Load simple program
    code = """
    addi r1, r0, 5
    addi r2, r0, 3
    add r3, r1, r2
    """
    
    instructions, errors = Assembler.assemble(code)
    assert len(errors) == 0, f"Assembly errors: {errors}"
    
    cpu.load_program(instructions)
    
    # Execute cycles (need enough cycles for pipeline to complete)
    for i in range(15):
        cpu.step()
    
    # Check results
    assert cpu.regs[1] == 5, f"r1 should be 5, got {cpu.regs[1]}"
    assert cpu.regs[2] == 3, f"r2 should be 3, got {cpu.regs[2]}"
    assert cpu.regs[3] == 8, f"r3 should be 8, got {cpu.regs[3]}"
    
    print("[PASS] Basic execution test passed")


def test_load_store():
    """Test load and store instructions"""
    cpu = CPU()
    
    code = """
    addi r1, r0, 10
    sw r1, 0(r0)
    lw r2, 0(r0)
    """
    
    instructions, errors = Assembler.assemble(code)
    assert len(errors) == 0
    
    cpu.load_program(instructions)
    
    for _ in range(10):
        cpu.step()
    
    assert cpu.data_mem[0] == 10, f"Memory[0] should be 10, got {cpu.data_mem[0]}"
    assert cpu.regs[2] == 10, f"r2 should be 10, got {cpu.regs[2]}"
    
    print("[PASS] Load/Store test passed")


def test_forwarding():
    """Test data forwarding"""
    cpu = CPU()
    
    code = """
    addi r1, r0, 5
    add r2, r1, r1
    add r3, r2, r2
    """
    
    instructions, errors = Assembler.assemble(code)
    cpu.load_program(instructions)
    
    for _ in range(15):
        cpu.step()
    
    assert cpu.regs[1] == 5
    assert cpu.regs[2] == 10
    assert cpu.regs[3] == 20
    
    print("[PASS] Forwarding test passed")


def test_load_use_stall():
    """Test load-use hazard detection and stalling"""
    cpu = CPU()
    
    code = """
    lw r1, 0(r0)
    add r2, r1, r1
    """
    
    instructions, errors = Assembler.assemble(code)
    cpu.load_program(instructions)
    
    # Set memory value
    cpu.data_mem[0] = 7
    
    # Execute and check for stall
    stall_detected = False
    for i in range(20):
        cpu.step()
        if cpu.hazard_info['stall']:
            stall_detected = True
    
    assert stall_detected, "Load-use stall should be detected"
    assert cpu.regs[2] == 14, f"r2 should be 14, got {cpu.regs[2]}"
    
    print("[PASS] Load-use stall test passed")


def test_branch():
    """Test branch instruction"""
    cpu = CPU()
    
    # PC=0: addi r1, r0, 5
    # PC=1: addi r2, r0, 5
    # PC=2: beq r1, r2, 3  (target = 2 + 3 = 5, skips PC=3,4)
    # PC=3: addi r3, r0, 1  (skipped)
    # PC=4: addi r4, r0, 2  (skipped)
    # PC=5: addi r5, r0, 3  (executed)
    code = """
    addi r1, r0, 5
    addi r2, r0, 5
    beq r1, r2, 3
    addi r3, r0, 1
    addi r4, r0, 2
    addi r5, r0, 3
    """
    
    instructions, errors = Assembler.assemble(code)
    cpu.load_program(instructions)
    
    for i in range(20):
        cpu.step()
    
    # Branch should skip addi r3 and addi r4
    assert cpu.regs[3] == 0, f"r3 should be 0 (skipped), got {cpu.regs[3]}"
    assert cpu.regs[4] == 0, f"r4 should be 0 (skipped), got {cpu.regs[4]}"
    assert cpu.regs[5] == 3, f"r5 should be 3, got {cpu.regs[5]}"
    
    print("[PASS] Branch test passed")


def test_jump():
    """Test jump instruction (absolute addressing)"""
    cpu = CPU()
    
    # PC=0: j 3         (target = absolute address 3)
    # PC=1: addi r1, r0, 1  (skipped)
    # PC=2: addi r2, r0, 2  (skipped)
    # PC=3: addi r3, r0, 3  (executed)
    code = """
    j 3
    addi r1, r0, 1
    addi r2, r0, 2
    addi r3, r0, 3
    """
    
    instructions, errors = Assembler.assemble(code)
    assert len(errors) == 0, f"Assembly errors: {errors}"
    cpu.load_program(instructions)
    
    for _ in range(15):
        cpu.step()
    
    # Jump should skip addi r1 and addi r2
    assert cpu.regs[1] == 0, "r1 should be 0 (skipped)"
    assert cpu.regs[2] == 0, "r2 should be 0 (skipped)"
    assert cpu.regs[3] == 3, "r3 should be 3"
    
    print("[PASS] Jump test passed")


def test_jump_with_label():
    """Test jump instruction with labels (PC-relative)"""
    cpu = CPU()
    
    # PC=0: addi r1, r0, 1
    # PC=1: j skip (skip is at PC=4, so offset = 4-1 = 3)
    # PC=2: addi r2, r0, 2 (skipped due to pipeline flush)
    # PC=3: addi r3, r0, 3 (skipped due to pipeline flush)
    # PC=4: addi r4, r0, 4
    code = """
    addi r1, r0, 1
    j skip
    addi r2, r0, 2
    addi r3, r0, 3
skip:
    addi r4, r0, 4
    """
    
    instructions, errors = Assembler.assemble(code)
    assert len(errors) == 0, f"Assembly errors: {errors}"
    cpu.load_program(instructions)
    
    for _ in range(15):
        cpu.step()
    
    # Jump should skip addi r2 and addi r3
    assert cpu.regs[1] == 1, "r1 should be 1"
    assert cpu.regs[2] == 0, "r2 should be 0 (skipped)"
    assert cpu.regs[3] == 0, "r3 should be 0 (skipped)"
    assert cpu.regs[4] == 4, "r4 should be 4"
    
    print("[PASS] Jump with label test passed")


def test_div_by_zero():
    """Test division by zero safety"""
    cpu = CPU()
    
    code = """
    addi r1, r0, 10
    addi r2, r0, 0
    div r3, r1, r2
    """
    
    instructions, errors = Assembler.assemble(code)
    cpu.load_program(instructions)
    
    for _ in range(15):
        cpu.step()
    
    # Should not crash, result should be 0
    assert cpu.regs[3] == 0, "Division by zero should result in 0"
    
    print("[PASS] Division by zero test passed")


def run_all_tests():
    """Run all tests"""
    print("Running CPU Core Tests...")
    print("-" * 40)
    
    test_basic_execution()
    test_load_store()
    test_forwarding()
    test_load_use_stall()
    test_branch()
    test_jump()
    test_jump_with_label()
    test_div_by_zero()
    
    print("-" * 40)
    print("All tests passed!")


if __name__ == '__main__':
    run_all_tests()


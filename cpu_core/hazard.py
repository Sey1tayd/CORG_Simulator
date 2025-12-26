"""
Hazard detection and forwarding logic
"""


class ForwardingUnit:
    """Handles data forwarding from EX/MEM and MEM/WB stages"""
    
    @staticmethod
    def compute(id_ex_rs, id_ex_rt, ex_mem_regwrite, ex_mem_rd, mem_wb_regwrite, mem_wb_rd):
        """
        Compute forwarding signals
        Returns: (forwardA, forwardB) where each is "00", "01", or "10"
        - "00": no forward (use ID/EX)
        - "10": forward from EX/MEM
        - "01": forward from MEM/WB
        """
        forward_a = "00"
        forward_b = "00"
        
        # ForwardA (for rs)
        if ex_mem_regwrite and ex_mem_rd != 0 and ex_mem_rd == id_ex_rs:
            forward_a = "10"  # From EX/MEM
        elif mem_wb_regwrite and mem_wb_rd != 0 and mem_wb_rd == id_ex_rs:
            forward_a = "01"  # From MEM/WB
        
        # ForwardB (for rt)
        if ex_mem_regwrite and ex_mem_rd != 0 and ex_mem_rd == id_ex_rt:
            forward_b = "10"  # From EX/MEM
        elif mem_wb_regwrite and mem_wb_rd != 0 and mem_wb_rd == id_ex_rt:
            forward_b = "01"  # From MEM/WB
        
        return forward_a, forward_b


class HazardDetectionUnit:
    """Detects load-use hazards"""
    
    @staticmethod
    def detect(id_ex_memread, id_ex_rt, if_id_rs, if_id_rt):
        """
        Detect load-use hazard
        Returns: (pc_write, if_id_write, id_ex_flush)
        """
        stall = False
        
        if id_ex_memread:
            if id_ex_rt == if_id_rs or id_ex_rt == if_id_rt:
                if id_ex_rt != 0:  # Don't stall for r0
                    stall = True
        
        return not stall, not stall, stall


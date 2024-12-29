from ReorderBuffer import ROB
from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
class InstructionQueue:
    def __init__(self, read_file_path):
        self.instructions = []
        with open(read_file_path, 'r') as file:
            for line in file:
                self.instructions.append(line.strip())
        self.op_queue = []# 记录指令信息
        for instruction in self.instructions:
            self.op_queue.append(instruction)
    
    def is_empty(self):
        return self.op_queue == []
    
    def issue(self, rob: ROB, register_file: RegisterFile, reservation_station: ReservationStation):
        # 不取指令的情况：队列或ROB已满
        if self.op_queue==[] or rob.is_full():
            return False
        
        instruction = self.op_queue.pop(0)
        
        if not reservation_station.is_full(instruction): # 发射到ROB中
            return rob.issue(instruction, register_file, reservation_station)
        else: # 不取指令的情况：指令对应保留站已满
            self.op_queue.insert(0,instruction)
            return False

        
from ReorderBuffer import ROB
from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
class InstructionQueue:
    #带有loop的怎么处理？
    def __init__(self, read_file_path):
        self.instructions = []
        with open(read_file_path, 'r') as file:
            for line in file:
                self.instructions.append(line.strip())
        self.op_queue = []
        for instruction in self.instructions:
            self.op_queue.append(instruction)
    
    def is_empty(self):
        return self.op_queue == []
    
    def issue(self, rob: ROB, register_file: RegisterFile, reservation_station: ReservationStation):
        # 怎么判断保留站满了没有？
        if self.op_queue==[] or rob.is_full():
            return False
        
        instruction = self.op_queue.pop(0)
        
            # 返回是否成功发射
        # TODO:如果此时后面还有指令需要存进来
        # 指令格式：fsub.d f8,f2,f6
        # 交给rob，再经由rob分别交给寄存器和保留站处理
        if not reservation_station.is_full(instruction): 
            return rob.issue(instruction, register_file, reservation_station)
        else:
            self.op_queue.insert(0,instruction)
            return False

        
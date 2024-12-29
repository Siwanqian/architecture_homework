from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
class InstructionQueue:
    def __init__(self, read_file_path):
        self.instructions = [] # 记录指令即对应地址
        self.check_dict = {
            'fld': 'Address', 'ld': 'Address', 'fadd.d': 'Add', 'addi': 'Int', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Address', 'bne': 'Int'
        }
        with open(read_file_path, 'r') as file:
            for line in file:
                addr = None
                if ':' in line:
                    l = line.split(':')
                    addr = l[0]
                    line = l[1]
                self.instructions.append((addr, line.strip()))
        self.op_queue = [] # 记录处理后的指令信息
        import re
        for instruction in self.instructions:
            ops = re.split(r'[ ,()]+', instruction[1])
            self.op_queue.append(tuple(ops))
    
    def import_instruction(self, addr): # 如果存在跳转指令，则导入跳转之后的指令
        flag = False
        import re
        for instruction in self.instructions:
            if instruction[0] == addr:
                flag = True
            if flag:
                ops = re.split(r'[ ,()]+', instruction[1])
                self.op_queue.append(tuple(ops))
                if ops[0] == 'bne':
                    break

    def is_empty(self):
        return self.op_queue == []
    

    def issue(self, register_file: RegisterFile, reservation_station: ReservationStation):
        # 不取指令的情况：队列已满
        if self.op_queue==[]:
            return False
        
        instruction = self.op_queue.pop(0)
        
        # 如果保留站未满
        if not reservation_station.is_full(instruction[0]): 
            result = reservation_station.issue(instruction, register_file)
        else:
            self.op_queue.insert(0,instruction)
            result = False
        
        # 如果有跳转指令
        if instruction[0] == 'bne':
            self.import_instruction(instruction[3])
        return result
        
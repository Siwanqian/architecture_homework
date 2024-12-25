from ReorderBuffer import ROB
from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
class InstructionQueue:
    #带有loop的怎么处理？
    def __init__(self, read_file_path):
        self.instructions = []
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
        self.op_queue = []
        import re
        for instruction in self.instructions:
            ops = re.split(r'[ ,()]+', instruction[1])
            self.op_queue.append(tuple(ops))
    
    def import_instruction(self, addr):
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
    
    def issue(self, rob: ROB, register_file: RegisterFile, reservation_station: ReservationStation):
        # 取出两条指令，如果是相同指令类型或者保留站不够用则拆分
        """
        不取指令的情况：opqueue为空或保留站满了或者reservation中的对应的第一条是满的
        取一条指令：opqueue只有一条指令或者保留站只有一个位置或者reservaion对应的第二条是满的或者第二条指令和第一条指令共用同一个发射站
        取两条：opqueue有两条指令且保留站有两个位置且reservation对应的两条都是空的
        """
        # 一条指令的情况
        if self.op_queue==[] or rob.is_full():
            return False

        ops0 = self.op_queue.pop(0)
        if reservation_station.is_full(ops0[0]):
            self.op_queue.insert(0, ops0)
            return False
        
        issue_bundle = None
        if ops0[0] == 'bne':
            self.import_instruction(ops0[3])
            issue_bundle = (ops0, )
            
        elif self.op_queue==[] or rob.get_empty_count()==1:
            issue_bundle = (ops0, )
        else:
            ops1 = self.op_queue.pop(0)
            if self.check_dict[ops0[0]]==self.check_dict[ops1[0]] or reservation_station.is_full(ops1[0]):
                issue_bundle = (ops0, )
                self.op_queue.insert(0, ops1)
            else:
                issue_bundle = (ops0, ops1)

        # TODO:如果此时后面还有指令需要存进来

        return rob.issue(issue_bundle, register_file, reservation_station)
        
if __name__ == '__main__':
    ins_op = InstructionQueue('python\ComputerArchitecture\Dual_spec\input.txt')
    print(ins_op.instructions)
    print(ins_op.op_queue)

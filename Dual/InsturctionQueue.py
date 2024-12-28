from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
from CDB import CDB

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
    
    def issue(self, register_file: RegisterFile, reservation_station: ReservationStation, cdb: CDB):
        # 取出两条指令，如果是相同指令类型或者保留站不够用则拆分
        """
        不取指令的情况：opqueue为空或reservation中的对应的第一条是满的
        取一条指令：opqueue只有一条指令或或者reservaion对应的第二条是满的或者第二条指令和第一条指令共用同一个类型的保留站或第一条指令是跳转指令，由于总是假设跳转，因此需要导入新的指令队列
        取两条：opqueue有两条指令且且reservation对应的两条都是空的
        """
        # 不取指令的情况：队列已满
        if self.op_queue==[]:
            return False

        # 不取指令的情况：第一条指令的对应保留站已满
        ops0 = self.op_queue.pop(0)
        if reservation_station.is_full(ops0[0]):
            self.op_queue.insert(0, ops0)
            return False
        
        issue_bundle = None

        # 取指令一条的情况：指令是跳转指令，需要导入新的指令队列
        if ops0[0] == 'bne':
            self.import_instruction(ops0[3])
            issue_bundle = (ops0, )
        # 取指令一条的情况：队列中只有一个空位
        elif self.op_queue == []:
            issue_bundle = (ops0, )
        else:
            ops1 = self.op_queue.pop(0)
            # 取指令一条的情况：第二条指令和第一条指令共用同一个保留站或者第二条指令需要的保留站已满
            if self.check_dict[ops0[0]]==self.check_dict[ops1[0]] or reservation_station.is_full(ops1[0]):
                issue_bundle = (ops0, )
                self.op_queue.insert(0, ops1)
            # 取指令两条的情况：其余的所有情况
            else:
                issue_bundle = (ops0, ops1)
                if ops1[0] == 'bne': # 如果第二条指令是转移指令，则导入新的指令队列
                    self.import_instruction(ops1[3])

        return reservation_station.issue(issue_bundle, register_file, cdb)
        
if __name__ == '__main__':
    ins_op = InstructionQueue('python\ComputerArchitecture\Dual_spec\input.txt')
    print(ins_op.instructions)
    print(ins_op.op_queue)

from InsturctionQueue import InstructionQueue
from ReservationStation import ReservationStation
from CDB import CDB
from RegisterFile import RegisterFile
from ReorderBuffer import ROB

class SIPS:
    def __init__(self, read_file_path):
        # 需要的模块：保留站 寄存器 ROB FP_OP_QUE CDB
        self.op_queue = InstructionQueue(read_file_path)
        self.reservation_station = ReservationStation()
        self.cdb = CDB()
        self.register_file= RegisterFile()
        self.rob = ROB(7)
        self.clock = 0
        self.comment = ""
    def run(self):
        while not self.op_queue.is_empty() or not self.rob.is_empty():
            self.clock+=1
            print(f"-------------------------------Clock {self.clock}-------------------------------\n")
            self.comment += f"-------------------------------Clock {self.clock}-------------------------------\n"
            self.rob.commit(self.register_file) # 提交
            self.rob.store_cdb(self.cdb) # 暂存数据
            self.cdb.clear() # 清除CDB中的数据
            self.reservation_station.execute(self.rob, self.cdb) # 执行
            self.rob.write_result(self.reservation_station) # 写结果
            self.op_queue.issue(self.rob, self.register_file, self.reservation_station) # 发射
                                                             
            self.comment += f"                           ROB\n"
            self.comment += self.rob.show() + '\n'
            self.comment += f"                         ReservationStation\n"
            self.comment += self.reservation_station.show() + '\n'
            self.comment += f"                                   Registers\n"
            self.comment += self.register_file.show() + '\n\n'
            if self.clock > 100: # 限制周期数
                break

        with open('python\ComputerArchitecture\Single_spec\output.txt', 'w') as file:
            file.write(self.comment)
            

if __name__ == '__main__':
    sips = SIPS('python\\ComputerArchitecture\\Single_spec\\input.txt')
    sips.run()
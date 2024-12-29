from InsturctionQueue import InstructionQueue
from ReservationStation import ReservationStation
from CDB import CDB
from RegisterFile import RegisterFile



class SIP:
    def __init__(self, read_file_path):
        # 需要的模块：保留站 寄存器 ROB FP_OP_QUE CDB
        self.op_queue = InstructionQueue(read_file_path)
        self.reservation_station = ReservationStation()
        self.cdb = CDB()
        self.register_file= RegisterFile()
        self.clock = 0
        self.comment = ""
    def run(self):
        while not self.op_queue.is_empty() or not self.reservation_station.is_empty():
            self.clock+=1
            print(f"-------------------------------Clock {self.clock}-------------------------------\n")
            self.comment += f"-------------------------------Clock {self.clock}-------------------------------\n"
            self.register_file.store_cdb(self.cdb, self.reservation_station) # 暂存CDB中的数据
            self.cdb.clear() # 清空CDB中的数据
            self.reservation_station.execute(self.cdb) # 执行
            self.register_file.write_result(self.reservation_station) # 写回结果
            self.op_queue.issue(self.register_file, self.reservation_station) # 发射
                                                             

            self.comment += f"                         ReservationStation\n"
            self.comment +=self.reservation_station.show() + '\n'
            self.comment += f"                                   Registers\n"
            self.comment +=self.register_file.show() + '\n\n'
            if self.clock > 100:
                break

        with open('python\ComputerArchitecture\Single\output.txt', 'w') as file:
            file.write(self.comment)
        

if __name__ == '__main__':
    sip = SIP('python\\ComputerArchitecture\\Single\\input.txt')
    sip.run()
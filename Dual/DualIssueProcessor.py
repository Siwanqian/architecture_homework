from InsturctionQueue import InstructionQueue
from ReservationStation import ReservationStation
from CDB import CDB
from RegisterFile import RegisterFile


class DIPS:
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

            self.register_file.write_result(self.reservation_station, self.cdb) # 写回结果
            self.op_queue.issue(self.register_file, self.reservation_station, self.cdb) # 发射
            self.cdb.clear() # 清空CDB中的数据
            self.reservation_station.execute(self.cdb) # 执行

            # 将功能单元中的本周期的新信息覆盖掉上一周期的信息
            self.reservation_station.recover_data()
            self.register_file.recover_data()

            self.comment += f"                         ReservationStation\n"
            self.comment += self.reservation_station.show() + '\n'
            self.comment += f"                                   Registers\n"
            self.comment += self.register_file.show() + '\n\n'
            if self.clock == 12: # 限制周期数
                break

        with open('python\ComputerArchitecture\Dual\output.txt', 'w') as file:
            file.write(self.comment)
        # print(self.reservation_station.memory_unit.Mem)
            

if __name__ == '__main__':
    dips = DIPS('python\\ComputerArchitecture\\Dual\\input.txt')
    dips.run()
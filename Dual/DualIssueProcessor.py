"""
假设写这里
1，3个浮点加法保留站，两个乘除保留站，2个整数单元，2个ld单元和2个sd单元
2，假设指令队列能够存储的数量为无限大
3，CDB是数据广播总线，从Unit到保留站
4，假设有十个寄存器
5，ROB一共有7项
6，在每个时钟周期内，执行顺序依次为：发射，提交，写回，执行
7，功能单元的个数
8，一个周期只能提交一个
9，address和memory共用同一个周期数
10，发射需要单独的一个周期
11，参照第四章part1ppt，执行和执行完成需要的周期数是分开的
"""
from InsturctionQueue import InstructionQueue
from ReservationStation import ReservationStation
from CDB import CDB
from RegisterFile import RegisterFile

            
# TODO:1，在哪里考虑loop跳转（发射的时候处理吗）
# 2, 对于ld和sd的第一个阶段，只要Vj存在就可以计算

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
        while not self.op_queue.is_empty() or not self.rob.is_empty():
            self.clock+=1
            print(f"-------------------------------Clock {self.clock}-------------------------------\n")
            self.comment += f"-------------------------------Clock {self.clock}-------------------------------\n"

            self.register_file.write_result(self.reservation_station, self.cdb)
            self.op_queue.issue(self.register_file, self.reservation_station, self.cdb)
            self.cdb.clear()
            self.reservation_station.execute(self.cdb)
            
            self.reservation_station.recover_data()
            self.register_file.recover_data()

            self.comment += f"                         ReservationStation\n"
            self.comment += self.reservation_station.show() + '\n'
            self.comment += f"                                   Registers\n"
            self.comment += self.register_file.show() + '\n\n'
            if self.clock == 19:
                break

        with open('python\ComputerArchitecture\Dual\output.txt', 'w') as file:
            file.write(self.comment)
            

if __name__ == '__main__':
    dips = DIPS('python\\ComputerArchitecture\\Dual\\input.txt')
    dips.run()
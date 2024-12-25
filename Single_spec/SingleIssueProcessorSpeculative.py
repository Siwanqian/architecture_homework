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
from ReorderBuffer import ROB


            
# TODO:1，在哪里考虑loop跳转（发射的时候处理吗）
# 2, sd写回还没有考虑
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
            self.rob.commit(self.register_file)
            self.rob.store_cdb(self.cdb)
            self.cdb.clear()
            self.reservation_station.execute(self.rob, self.cdb)
            self.rob.write_result(self.reservation_station)
            self.op_queue.issue(self.rob, self.register_file, self.reservation_station)
                                                             
            self.comment += f"                           ROB\n"
            self.comment += self.rob.show() + '\n'
            self.comment += f"                         ReservationStation\n"
            self.comment += self.reservation_station.show() + '\n'
            self.comment += f"                                   Registers\n"
            self.comment += self.register_file.show() + '\n\n'
            if self.clock > 100:
                break

        with open('python\ComputerArchitecture\Single_spec\output.txt', 'w') as file:
            file.write(self.comment)
            

if __name__ == '__main__':
    sips = SIPS('python\\ComputerArchitecture\\Single_spec\\input.txt')
    sips.run()
from CDB import CDB

class FPAdder:
    def __init__(self):
        self.busy = False
        self.delay_time = 2
        self.remain_time = 0
        self.Op = None
        self.Vj = None
        self.Vk = None
        self.dest = None

    def issue_instruction(self, Op, Vj, Vk, dest): # 将指令发射入执行单元并对执行单元设忙碌
        if self.busy:
            raise ValueError('错误使用忙碌加法单元')
        self.Op = Op
        self.remain_time = self.delay_time
        self.Vj = Vj
        self.Vk = Vk
        self.dest = dest
        self.busy = True
    
    def is_busy(self): # 检测执行单元是否忙碌
        return self.busy

    def execute(self, cdb: CDB, rob): # 执行操作，将剩余的执行周期减1，如果执行完成则广播数据
        if self.busy and self.remain_time == self.delay_time:
            rob.change_state(self.dest, 'Execute')
        if self.busy and self.remain_time > 0:
            self.remain_time -= 1
        
        if self.busy and self.remain_time == 0 and not cdb.is_full():
            value = int(self.Vj) + int(self.Vk) if self.Op == 'fadd,d' else int(self.Vj) - int(self.Vk)
            cdb.broadcast(self.dest, value)
            self.busy = False
            return
        

class FPMultiplier:
    def __init__(self):
        self.busy = False
        self.delay_time = {'fmul.d': 6, 'fdiv.d': 12}
        self.remain_time = 0
        self.Op = None
        self.Vj = None
        self.Vk = None
        self.dest = None

    def issue_instruction(self, Op, Vj, Vk, dest): # 将指令发射入执行单元并对执行单元设忙碌
        if self.busy:
            raise ValueError('错误使用忙碌乘法单元')
        if Op not in self.delay_time:
            raise ValueError('乘法操作存在未定义操作{}'.format(Op))
        self.Op = Op
        self.remain_time = self.delay_time[Op]
        self.Vj = Vj
        self.Vk = Vk
        self.dest = dest
        self.busy = True
    
    def is_busy(self): # 检测执行单元是否忙碌
        return self.busy

    def execute(self, cdb: CDB, rob): # 执行操作，将剩余的执行周期减1，如果执行完成则广播数据
        if self.busy and self.remain_time == self.delay_time[self.Op]:
            rob.change_state(self.dest, 'Execute')
        if self.busy and self.remain_time > 0:
            self.remain_time -= 1

        if self.busy and self.remain_time == 0 and not cdb.is_full():
            value = int(self.Vj) * int(self.Vk) if self.Op == 'fmult.d' else int(self.Vj) / int(self.Vk)
            cdb.broadcast(self.dest, value)
            self.busy = False
            return


class AddressUnit:
    def __init__(self):
        self.busy = False
        self.A = None
        self.Vj = None
        self.entry = None

    def issue_instruction(self, A, Vj, entry): # 将指令发射入执行单元并对执行单元设忙碌
        if self.busy:
            raise ValueError('错误使用忙碌地址单元')
        self.A = A
        self.Vj = Vj
        self.busy = True
        self.entry = entry
    
    def is_busy(self): # 检测执行单元是否忙碌
        return self.busy

    def execute(self, reservation_station): # 执行操作，并写入地址单元
        if not self.busy:
            return
        # print(self.entry)
        self.entry['A'] = int(self.Vj) + int(self.A)
        reservation_station.change_state(self.entry['Name'], 'Execute')
        self.busy = False


class MemoryUnit:
    def __init__(self):
        self.Mem = {i: 123 for i in range(1000, 1033, 8)}
        self.busy = False
        self.addr = None
        self.dest = None

    def issue_instruction(self, addr: str, dest: str): # 将指令发射入执行单元并对执行单元设忙碌
        self.addr = addr
        self.dest = dest
        self.busy = True

    def is_busy(self): # 检测执行单元是否忙碌
        return self.busy

    def execute(self, cdb: CDB, reservation_station): # 执行操作并广播数据
        if not self.busy:
            return
        if not cdb.is_full():
            if self.addr not in self.Mem:
                self.Mem[self.addr] = 1
                # raise ValueError('存在未定义存储器{}'.format(self.addr))
            reservation_station.change_state(self.dest, 'MemoryAccess')
            cdb.broadcast(self.dest, self.Mem[self.addr])
            self.busy = False



class IntegerUnit:
    def __init__(self):
        self.busy = False
        self.delay_time = 1
        self.remain_time = 0
        self.Op = None
        self.Vj = None
        self.Vk = None
        self.dest = None

    def issue_instruction(self, Op, Vj, Vk, dest): # 将指令发射入执行单元并对执行单元设忙碌
        if self.busy:
            raise ValueError('错误使用忙碌加法单元')
        self.Op = Op
        self.remain_time = self.delay_time
        self.Vj = Vj
        self.Vk = Vk
        self.dest = dest
        self.busy = True
    
    def is_busy(self): # 检测执行单元是否忙碌
        return self.busy

    def execute(self, cdb: CDB, reservation_station): # 执行操作，将剩余的执行周期减1，如果执行完成则广播数据
        if self.busy and self.remain_time == self.delay_time:
            reservation_station.change_state(self.dest, 'Execute')
        if self.busy and self.remain_time > 0:
            self.remain_time -= 1
        
        if self.busy and self.remain_time == 0 and not cdb.is_full():
            value = None
            if self.Op == 'addi':
                value = int(self.Vj) + int(self.Vk)  
            elif self.Op == 'bne':
                value = int(self.Vj) - int(self.Vk)  
            
            cdb.broadcast(self.dest, value)
            self.busy = False
            return
import copy
from ReservationStation import ReservationStation
from RegisterFile import RegisterFile
from prettytable import PrettyTable
from CDB import CDB
class ROB:
    def __init__(self, entries_num: int):
        self.entries = [
            {'Entry': str(i), 'Busy': False, 'Instruction': None, 'State': None, 'Dest': None, 'Value': None
            } for i in range(1, entries_num+1)]
        self.entries.insert(0, None)

        self.entries_num = entries_num
        self.head = 1 # ROB的未提交的第一条条目
        self.tail = 1 # ROB中非忙碌状态的第一条条目
        self.old_entries = copy.deepcopy(self.entries)
        self.old_head = self.head
        self.old_tail = self.tail

    def is_full(self): # 检测上一周期中ROB是否已满
        if self.old_tail ==self.old_head and self.old_entries[self.old_head]['Busy']:
            return True
        return False
    
    def is_empty(self): # 检测上一周期中ROB是否为空
        if self.old_tail == self.old_head and not self.old_entries[self.old_head]['Busy']:
            return True
        return False
    
    def get_empty_count(self): # 检测上一周期中ROB的空闲表项
        print(self.old_head, self.old_tail)
        if self.is_full():
            return 0
        elif self.is_empty():
            return self.entries_num
        else:
            return (self.entries_num - (self.old_tail-self.old_head)) % self.entries_num

    def issue(self, issue_bundle: tuple, register_file: RegisterFile, reservation_station: ReservationStation, cdb: CDB):
        if self.entries[self.tail]['Busy']:
            raise ValueError("ROB模块issue异常发射")
        
        # 分析两条共同发射的指令之间是否存在指令关联
        # 再将两条指令同时发射

        bundle_size = len(issue_bundle)
        # 记录冲突信息
        dependence = {}
        entries = None
        if bundle_size == 2: # 如果是两条指令同时发射，则需要分析指令之间的依赖关系
            # 作为第一条指令
            # ld指令：op[1]需要被分析
            # sd指令：没有需要被分析的
            # alu指令：op[1]
            # bne：不需要分析
            # 第二条指令
            # ld指令：分析op[3]与上一条
            # sd指令：分析op[1]和op[3]的关联
            # alu：分析op[2]、op[3]的关联
            # bne：分析op[1]、op[2]
            ops0 = issue_bundle[0]
            ops1 = issue_bundle[1]
            if ops0[0] != 'sd' and ops0[0] != 'bne':
                if ops1[1] == ops0[1]:
                    if ops1[0]=='sd' or ops1[0]=='bne':
                        dependence[ops1[1]] = ops0[1]
                if ops1[2] == ops0[1]:
                    if ops1[0]=='addi' or ops1[0] == 'add' or ops1[0]=='mult' or ops1[0]=='bne':
                        dependence[ops1[2]] = ops0[1]
                if ops1[3] == ops0[1]:
                    if ops1[0]=='ld' or ops1[0]=='sd'or ops1[0]=='addi' or ops1[0] == 'add' or ops1[0]=='mult':
                        dependence[ops1[3]] = ops0[1]
            entries = [self.tail, self.tail%self.entries_num+1]
        elif bundle_size == 1:
            entries = [self.tail, ]
        else:
            raise ValueError


        # 保留站发射
        reservation_station.set_station(register_file, issue_bundle, self, dependence, entries, cdb)
        
        # 设置第一条指令的相关信息
        self.entries[self.tail]['Busy'] = True
        self.entries[self.tail]['Instruction'] = ' '.join(issue_bundle[0])
        self.entries[self.tail]['State'] = 'Issue'
        if issue_bundle[0][0]=='sd':
            self.entries[self.tail]['Dest'] = '{}({})'.format(issue_bundle[0][2],issue_bundle[0][3])
        elif issue_bundle[0][0]=='bne':
            self.entries[self.tail]['Dest'] = None
        else:
            self.entries[self.tail]['Dest'] = issue_bundle[0][1]
        self.entries[self.tail]['Value'] = None
        # 寄存器模块，如果不是sd和bne指令，其余指令都存在写寄存器操作
        if issue_bundle[0][0] != 'sd' and issue_bundle[0][0] != 'bne':
            register_file.set_registers(issue_bundle[0][1], self.entries[self.tail]['Entry'])

        self.tail = self.tail % self.entries_num + 1

        if bundle_size == 2: # 如果同时发射两条指令，则设置第二条指令的对应信息
            self.entries[self.tail]['Busy'] = True
            self.entries[self.tail]['Instruction'] = ' '.join(issue_bundle[1])
            self.entries[self.tail]['State'] = 'Issue'
            if issue_bundle[1][0]=='sd':
                self.entries[self.tail]['Dest'] = '{}({})'.format(issue_bundle[1][2],issue_bundle[1][3])
            elif issue_bundle[1][0]=='bne':
                self.entries[self.tail]['Dest'] = None
            else:
                self.entries[self.tail]['Dest'] = issue_bundle[1][1]
                self.entries[self.tail]['Value'] = None
            # 寄存器模块
            if issue_bundle[1][0] != 'sd' and issue_bundle[1][0] != 'bne':
                register_file.set_registers(issue_bundle[1][1], self.entries[self.tail]['Entry'])

            self.tail = self.tail % self.entries_num + 1
        return True
    
    def commit(self, register_file: RegisterFile, reservation_station: ReservationStation, cdb: CDB):
        # 保留站中没有数据则不需要提交
        if self.is_empty():
            return
        
        entry = self.entries[self.head] # 获取head条目

        datas = cdb.get_data()
        # bne的结果直接提交即可
        for data in datas:
            if self.entries[int(data['Dest'])]['Instruction'].split()[0] == 'bne':
                self.entries[int(data['Dest'])]['Value'] = data['Value']

        # 如果head条目可以发射
        if entry['Busy'] and (entry['State'] in ['WriteResult', 'Commit'] 
                                                or (entry['Instruction'].split()[0] == 'sd' and reservation_station.is_store_able(self.head))
                                                or (entry['Instruction'].split()[0] == 'bne' and entry['Value'] != None)):
            op = entry['Instruction'].split()[0]
            # 如果此时的寄存器还是他，把他设为不忙碌
            if op == 'bne':
                if entry['Value'] == 0:
                    pass # 由于假设转移指令的假设是永远正确的，因此这个地方可以重复处理
            if op == 'sd': # 写回存储器中
                reservation_station.write_store_back(self.entries[self.head], self.head)
            else: # 设置寄存器的值
                register_file.set_reg_value(self.entries[self.head]['Dest'], self.entries[self.head]['Value'])
            # 释放寄存器
            register_file.free_reg(self.entries[self.head]['Dest'], self.entries[self.head]['Entry'])
            # 释放保留站的条目
            self.entries[self.head]['Busy'] = False
            self.entries[self.head]['State'] = 'Commit'

            # 处理第二条head条目
            ent2 = self.head % self.entries_num + 1
            entry = self.entries[ent2]
            
            if entry['Busy'] and (entry['State'] in ['WriteResult', 'Commit'] 
                                               or (entry['Instruction'].split()[0] == 'sd' and reservation_station.is_store_able(ent2))
                                               or entry['Instruction'].split()[0] == 'bne' and entry['Value'] != None):
                op = entry['Instruction'].split()[0]
                # 如果此时的寄存器还是他，把他设为不忙碌
                if op == 'bne':
                    if entry['Value'] == 0:
                        pass
                if op == 'sd':
                    reservation_station.write_store_back(entry, ent2)
                else:
                    register_file.set_reg_value(entry['Dest'], entry['Value'])
                register_file.free_reg(entry['Dest'], entry['Entry'])
                entry['Busy'] = False
                entry['State'] = 'Commit'
                self.head = (self.head+1)%self.entries_num+1
            else: # 如果第二条不能提交，则head只加1
                self.head = (self.head)%self.entries_num+1
                
        

    def get_state(self, index: str): # 获取表项状态
        return self.old_entries[int(index)]['State']
    
    def change_state(self, index: str, state: str): # 更改表项状态
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        self.entries[int(index)]['State'] = state
    
    def check_dest_state(self, reorder): # 检查目标表项是否已经写回
        if self.old_entries[int(reorder)]['State'] in ['WriteResult', 'Commit']:
            # 如果已经写回，返回数值
            return self.old_entries[int(reorder)]['Value']
        # 如果为写回，返回未准备好
        return 'NotReady'

    def write_result(self, reservation_station: ReservationStation, cdb: CDB):
        if cdb.is_empty(): # 当cdb为空时则没有可写回的
            return
        cdb_data = cdb.get_data() # 获取cdb中的数据
        # self.temp_data = cdb.get_data()
        for data in cdb_data: # 将数据写入ROB中
            self.entries[int(data['Dest'])]['Value'] = data['Value']
            # bne不需要设置成写回状态
            if self.entries[int(data['Dest'])]['Instruction'].split()[0] != 'bne':
                self.entries[int(data['Dest'])]['State'] = 'WriteResult'
        
        reservation_station.write_result(cdb_data)

    
    def recover_data(self): # 更新旧表项
        self.old_entries = copy.deepcopy(self.entries)
        self.old_head = self.head
        self.old_tail = self.tail

    
    def show(self):
        head = ['Entry', 'Busy', 'Instruction', 'State', 'Dest', 'Value']
        table = PrettyTable(head)

        for i in range(1, self.entries_num+1):
            ent = []
            entry = self.entries[i]
            for title in head:
                ent.append(entry[title])
            table.add_row(ent)


        print(table)
        return str(table)

if __name__ == '__main__':
    rob = ROB(7)
    # rob.issue('fld f6,32(x2)')
    rob.show()
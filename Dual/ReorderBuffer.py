import re
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

        self.temp_data = None
        self.entries_num = entries_num
        self.head = 1
        self.tail = 1

    def is_full(self):
        if self.tail ==self.head and self.entries[self.head]['Busy']:
            return True
        return False
    
    def is_empty(self):
        if self.tail ==self.head and not self.entries[self.head]['Busy']:
            return True
        return False
    
    def get_empty_count(self):
        if self.is_full():
            return 0
        elif self.is_empty():
            return self.entries_num
        else:
            return (self.tail-self.head) % self.entries_num
        
    """def allocate_pos(self, num: int):
        if num > 2 or num <= 0 or self.get_empty_count() < num:
            raise ValueError('非法num')
        entry = []
        for i in range(num):
            entry.append(self.entries[(self.tail+i)%self.entries_num+1])
        return entry"""

    def issue(self, issue_bundle: tuple, register_file: RegisterFile, reservation_station: ReservationStation):
        if self.entries[self.tail]['Busy']:
            raise ValueError("ROB模块issue异常发射")
        
        # 分析两条共同发射的指令之间是否存在指令关联
        # 再将两条指令同时发射

        """
        Loop: ld x2,0(x1)
        addi x2,x2,1
        sd x2,0(x1)
        addi x1,x1,8
        bne x2,x3,Loop
        """

        bundle_size = len(issue_bundle)
        # 记录冲突信息
        dependence = {}
        entries = None
        if bundle_size == 2:
            # 作为第一条指令
            # ld指令：op[1]需要被分析
            # sd指令：没有需要被分析的
            # alu指令：op[1]
            # bne：不需要分析 TODO：仅指在存在保留站中
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


        # 保留站
        reservation_station.set_station(register_file, issue_bundle, self, dependence, entries)
        

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
        # 寄存器模块
        if issue_bundle[0][0] != 'sd' and issue_bundle[0][0] != 'bne':
            register_file.set_registers(issue_bundle[0][1], self.entries[self.tail]['Entry'])

        self.tail = self.tail % self.entries_num + 1

        if bundle_size == 2:
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
        if self.is_empty():
            return
        
        entry = self.entries[self.head]

        datas = cdb.get_data()
        for data in datas:
            if self.entries[int(data['Dest'])]['Instruction'].split()[0] == 'bne':
                self.entries[int(data['Dest'])]['Value'] = data['Value']

        if entry['Busy'] and (entry['State'] in ['WriteResult', 'Commit'] 
                                                or (entry['Instruction'].split()[0] == 'sd' and reservation_station.is_store_able(self.head))
                                                or (entry['Instruction'].split()[0] == 'bne' and entry['Value'] != None)):
            op = entry['Instruction'].split()[0]
            # 如果此时的寄存器还是他，把他设为不忙碌
            if op == 'bne':
                if entry['Value'] == 0:
                    pass
            if op == 'sd':
                reservation_station.write_store_back(self.entries[self.head], self.head)
            else:
                register_file.set_reg(self.entries[self.head]['Dest'], self.entries[self.head]['Value'])
            register_file.free_reg(self.entries[self.head]['Dest'], self.entries[self.head]['Entry'])
            self.entries[self.head]['Busy'] = False
            self.entries[self.head]['State'] = 'Commit'

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
                    register_file.set_reg(entry['Dest'], entry['Value'])
                register_file.free_reg(entry['Dest'], entry['Entry'])
                entry['Busy'] = False
                entry['State'] = 'Commit'
                self.head = (self.head+1)%self.entries_num+1
            else:
                self.head = (self.head)%self.entries_num+1
                
        

    def get_state(self, index: str):
        return self.entries[int(index)]['State']
    
    def change_state(self, index: str, state: str):
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        self.entries[int(index)]['State'] = state
    
    def check_dest_state(self, reorder):
        if self.entries[int(reorder)]['State'] in ['WriteResult', 'Commit']:
            return self.entries[int(reorder)]['Value']
        
        return 'NotReady'

    def store_cdb(self, cdb: CDB):
        if cdb.is_empty():
            self.temp_data = None
            return
        import copy
        self.temp_data = copy.deepcopy(cdb.get_data())
        # self.temp_data = cdb.get_data()
        for data in self.temp_data:
            if self.entries[int(data['Dest'])]['Instruction'].split()[0] != 'bne':
                self.entries[int(data['Dest'])]['State'] = 'WriteResult'

    def write_result(self, reservation_station: ReservationStation):
        # 从cdb中读取结果并写在rob上，然后更新regstation
        # 返回的data：dest、
        if self.temp_data != None:
            for data in self.temp_data:
                self.entries[int(data['Dest'])]['Value'] = data['Value']
                # data['Value'] = 'Regs[{}]'.format(self.entries[int(data['Dest'])]['Dest'])
                # 写回reservation_station
    
                reservation_station.write_result(self.temp_data)

    
    def show(self):
        # reload(sys)
        # sys.setdefaultencoding('utf8')
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
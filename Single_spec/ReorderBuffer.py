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

    def issue(self, instruction: str, register_file: RegisterFile, reservation_station: ReservationStation):
        if self.entries[self.tail]['Busy']:
            raise ValueError("ROB模块issue异常发射")
        
        ops = re.split(r'[ ,()]+', instruction)
        self.entries[self.tail]['Busy'] = True
        self.entries[self.tail]['Instruction'] = instruction
        self.entries[self.tail]['State'] = 'Issue'
        self.entries[self.tail]['Dest'] = ops[1] if ops[0] != 'fsd' else None
        self.entries[self.tail]['Value'] = None
        
        # 保留站
        reservation_station.set_station(register_file, ops, self.entries[self.tail]['Entry'], self)

        # 寄存器模块
        if ops[0] != 'fsd':
            register_file.set_registers(ops[1], self.entries[self.tail]['Entry'])
        

        self.tail = self.tail % self.entries_num + 1
        return True
    
    def commit(self, register_file: RegisterFile):
        if self.is_empty():
            return

        if self.entries[self.head]['Busy'] and self.entries[self.head]['State'] == 'WriteResult':
            # 如果此时的寄存器还是他，把他设为不忙碌
            register_file.free_reg(self.entries[self.head]['Dest'], self.entries[self.head]['Entry'])
            self.entries[self.head]['Busy'] = False
            self.entries[self.head]['State'] = 'Commit'
            self.head = self.head % self.entries_num + 1

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
        if not cdb.is_busy():
            self.temp_data = None
            return
        self.temp_data = cdb.get_data()
        self.entries[int(self.temp_data['Dest'])]['State'] = 'WriteResult'

    def write_result(self, reservation_station: ReservationStation):
        # 从cdb中读取结果并写在rob上，然后更新regstation
        # 返回的data：dest、
        if self.temp_data == None:
            return
        
        data = self.temp_data
        self.entries[int(data['Dest'])]['Value'] = data['Value']
        data['Value'] = 'Regs[{}]'.format(self.entries[int(data['Dest'])]['Dest'])
        self.entries[int(data['Dest'])]['State'] = 'WriteResult'
        # 写回reservation_station
        reservation_station.write_result(data)
    
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
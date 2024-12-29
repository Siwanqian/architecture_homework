from prettytable import PrettyTable
from CDB import CDB
import copy
class RegisterFile:
    def __init__(self):
        self.register_file = {'x{}'.format(j): {'Qi': None, 'Busy': False, 'Value': 1} for j in range(1, 4)}
        """self.register_file = {**{'f{}'.format(i): {'Qi': None, 'Busy': False, 'Value': 1} for i in range(0, 11)},
                              **{'x{}'.format(j): {'Qi': None, 'Busy': False, 'Value': 1} for j in range(1, 4)}
                              }"""
        self.register_file['x1']['Value'] = 1000
        self.old_register_file = copy.deepcopy(self.register_file)

    def set_registers(self, reg: str, Qi: str): # 设置寄存器为忙碌
        if reg not in self.register_file:
            raise ValueError('向寄存器组传递了不存在的寄存器')
        self.register_file[reg]['Qi'] = Qi
        self.register_file[reg]['Busy'] = True

    def registers(self): # 返回寄存器组
        return self.register_file.keys()
    
    def get_value(self, reg): # 获取对应寄存器的值
        return self.old_register_file[reg]['Value']
    
    def set_reg_value(self, reg: str, value: str): # 设置寄存器的值
        if reg not in self.registers():
            return
        
        self.register_file[reg]['Value'] = value
        
        return

    def check_reg_state(self, reg: str):# 如果繁忙会返回对应的保留站条目，否则会返回'Free'
        if reg not in self.registers():
            raise ValueError('RegisterFile类检查到错误寄存器{}'.format(reg))
        
        if self.old_register_file[reg]['Busy']:
            return self.old_register_file[reg]['Qi']
        
        return 'Free'
    
    def free_reg(self, reg: str, Qi: str): # 如果是最后一条写入的保留站表项，释放寄存器
        if reg not in self.registers():
            return
        
        if self.register_file[reg]['Qi']==Qi:
            self.register_file[reg]['Busy'] = False
        
        return



    def write_result(self, reservation_station, cdb: CDB): # 从cdb中获取数据信息并写回
        reservation_station.check_store()
        if cdb.is_empty():
            return
        cdb_data = cdb.get_data()

        for data in cdb_data:
            for reg in self.register_file.values():
                if reg['Qi'] == data['Dest']:
                    reg['Value'] = data['Value']
                    reg['Busy'] = False
        reservation_station.write_result(cdb_data)

    def recover_data(self):
        self.old_register_file = copy.deepcopy(self.register_file)

    def show(self):
        # reload(sys)
        # sys.setdefaultencoding('utf8')
        head = []
        for reg in self.register_file:
            head.append(reg)
        head.insert(0, 'Reg')
        table = PrettyTable(head)

        row = ['Qi']
        for reg in self.register_file: 
            row.append(self.register_file[reg][row[0]])
        table.add_row(row)

        row = ['Busy']
        for reg in self.register_file: 
            row.append(self.register_file[reg][row[0]])
        table.add_row(row)

        row = ['Value']
        for reg in self.register_file: 
            row.append(self.register_file[reg][row[0]])
        table.add_row(row)

        print(table)
        return str(table)

if __name__ == '__main__':
    reg = RegisterFile()
    # reg.set_registers('f0', 5)
    reg.show()
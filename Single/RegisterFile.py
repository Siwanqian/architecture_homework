from prettytable import PrettyTable
from CDB import CDB
class RegisterFile:
    def __init__(self):
        self.register_file = {**{'f{}'.format(i): {'Qi': None, 'Busy': False, 'Value' : 0} for i in range(0, 11)},
                              **{'x{}'.format(j): {'Qi': None, 'Busy': False, 'Value' : 0} for j in range(1, 4)}
                              }
        self.regs = [i for i in self.register_file]
        self.temp_data = None

    def set_registers(self, reg: str, Qi: str): # 设置寄存器为忙碌
        if reg not in self.register_file:
            raise ValueError('向寄存器组传递了不存在的寄存器')
        self.register_file[reg]['Qi'] = Qi
        self.register_file[reg]['Busy'] = True

    def registers(self): # 返回寄存器组
        return self.regs
    
    def check_reg_state(self, reg: str):# 如果繁忙会返回对应的重排序，否则会返回'Free'
        if reg not in self.regs:
            raise ValueError('RegisterFile类检查到错误寄存器')
        
        if self.register_file[reg]['Busy']:
            return self.register_file[reg]['Qi']
        
        return 'Free'
    
    def free_reg(self, reg: str, Qi: str): # 如果是最后一条写入的保留站表项，释放寄存器
        if reg not in self.regs:
            return
        
        if not self.register_file[reg]['Busy']:
            raise ValueError('错误释放寄存器')
        if self.register_file[reg]['Qi']==Qi:
            self.register_file[reg]['Busy'] = False
        
        return
    
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
    
    def store_cdb(self, cdb: CDB, reservation_station):
        if not cdb.is_busy():
            self.temp_data = None
            return
        self.temp_data = cdb.get_data()
        reservation_station.store_cdb(self.temp_data)

    def write_result(self, reservation_station):
        if self.temp_data == None:
            return
        r = None
        for name, reg in self.register_file.items():
            if reg['Qi'] == self.temp_data['Dest']:
                reg['Value'] = self.temp_data['Value']
                reg['Busy'] = False
                r = name
        reservation_station.write_result({'Dest': self.temp_data['Dest'], 'Value':'Regs[{}]'.format(r)})

if __name__ == '__main__':
    reg = RegisterFile()
    # reg.set_registers('f0', 5)
    print(reg.regs)
from prettytable import PrettyTable
class RegisterFile:
    def __init__(self):
        # 'x{} {}'.format(str(i+1),str(1))
        self.register_file = {**{'f{}'.format(i): {'Reorder': None, 'Busy': False} for i in range(0, 11)},
                              **{'x{}'.format(j): {'Reorder': None, 'Busy': False} for j in range(1, 4)}
                              }
        self.regs = [i for i in self.register_file]

    def set_registers(self, reg: str, reorder: str):
        if reg not in self.register_file:
            raise ValueError('向寄存器组传递了不存在的寄存器')
        self.register_file[reg] = {
            'Reorder': reorder,
            'Busy': True
        }

    def registers(self):
        return self.regs
    
    def check_reg_state(self, reg: str):# 如果繁忙会返回对应的重排序，否则会返回'Free'
        if reg not in self.regs:
            raise ValueError('RegisterFile类检查到错误寄存器')
        
        if self.register_file[reg]['Busy']:
            return self.register_file[reg]['Reorder']
        
        return 'Free'
    
    def free_reg(self, reg: str, reorder: str):
        if reg not in self.regs:
            return
        
        if not self.register_file[reg]['Busy']:
            raise ValueError('错误释放寄存器')
        if self.register_file[reg]['Reorder']==reorder:
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

        row = ['Reorder']
        for reg in self.register_file: 
            row.append(self.register_file[reg][row[0]])
        table.add_row(row)

        row = ['Busy']
        for reg in self.register_file: 
            row.append(self.register_file[reg][row[0]])
        table.add_row(row)

        print(table)
        return str(table)

if __name__ == '__main__':
    reg = RegisterFile()
    # reg.set_registers('f0', 5)
    reg.show()
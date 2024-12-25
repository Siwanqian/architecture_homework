from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB
import re

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，两个乘除保留站，2个整数单元，2个ld单元和2个sd单元
        self.entries = {
            'Load':[
                {'Name': 'Load{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None} for i in range(1,3)
            ],
            'Add':[
                {'Name': 'Add{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None} for i in range(1,4)
            ],
            'Mult':[
                {'Name': 'Mult{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None} for i in range(1,3)
            ],
            'Store':[
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None} for i in range(1,3)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None} for i in range(1,3)
            ]
        }
        self.check_dict = {
            'fld': 'Load', 'ld': 'Load', 'fadd.d': 'Add', 'addi': 'Add', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Store'
        }
        self.fp_adder = FPAdder()
        self.fp_multipliers = FPMultiplier()
        self.address_unit = AddressUnit()
        self.memory_unit = MemoryUnit()
        self.integer_unit = IntegerUnit()

    def is_full(self, instruction: str):
        op = instruction.split()[0]

        if op not in self.check_dict:
            raise ValueError('保留站类is_full函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]
        for entry in self.entries[entry_name]:
            if entry['Busy'] == False:
                return False
        return True
    
    def is_empty(self):
        for unit in self.entries.values():
            for entry in unit:
                if entry['Busy'] == True:
                    return False
        return True
    def execute(self, cdb: CDB):
        for unit in self.entries.values():
            for entry in unit:
                # TODO：这个地方需要判断他是不是在发射阶段吗
                exec_unit = None
                if not entry['Busy']:
                    continue
                if self.check_dict[entry['Op']] == 'Add':
                    if entry['Busy'] and entry['Qj']==None and entry['Qk']==None and entry['State'] == 'Issue':
                        exec_unit = self.fp_adder
                    else:
                        continue
                elif self.check_dict[entry['Op']] == 'Mult':
                    if entry['Busy'] and entry['Qj']==None and entry['Qk']==None and entry['State'] == 'Issue':
                        exec_unit = self.fp_multipliers
                    else:
                        continue
                elif self.check_dict[entry['Op']] == 'Load' or self.check_dict[entry['Op']] == 'Store':
                    if not entry['Busy'] or entry['Qj']!=None:
                        continue
                    if entry['State'] == 'Issue':
                        exec_unit = self.address_unit
                    elif entry['State'] == 'Execute' and self.check_dict[entry['Op']] == 'Load':
                        exec_unit = self.memory_unit
                    else:
                        continue
                elif entry['Op'] in self.check_dict:
                    continue
                else:
                    raise ValueError('{}功能单元未定义'.format(entry['Op']))

                if not exec_unit.is_busy():
                    if self.check_dict[entry['Op']] == 'Load':
                        if entry['State'] == 'Issue':
                            exec_unit.issue_instruction(entry['A'], entry['Vj'], entry)
                        elif entry['State'] == 'Execute':
                            exec_unit.issue_instruction(entry['A'], entry['Name'])
                    elif self.check_dict[entry['Op']] == 'Store':
                        exec_unit.issue_instruction(entry['A'], entry['Vj'], entry['Name'])
                    else:
                        exec_unit.issue_instruction(entry['Op'], entry['Vj'], entry['Vk'], entry['Name'])
        self.fp_adder.execute(cdb, self)
        self.fp_multipliers.execute(cdb, self)
        self.address_unit.execute(self)
        self.integer_unit.execute(cdb, self)
        self.memory_unit.execute(cdb, self)


    def change_state(self, dest: str, state: str):
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        for unit in self.entries.values():
            for entry in unit:
                if entry['Name'] == dest:
                    entry['State'] = state

    def issue(self, instruction: str, register_file: RegisterFile):
        ops = re.split(r'[ ,()]+', instruction)
        op = ops[0]
        if op not in self.check_dict:
            raise ValueError('保留站类set_station函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]

        entry = None
        for ent in self.entries[entry_name]:
            if ent['Busy'] == False:
                entry = ent
                break
        if entry == None:
            raise ValueError('保留站类set_station函数{}类型条目已满'.format(entry_name))    
        
        entry['Busy'] = True
        entry['Op'] = op
        # ld x2,0(x1)
        # sd x2,0(x1)
        if entry_name == 'Load' or entry_name == 'Store':
            entry['A'] = ops[2]
            if register_file.check_reg_state(ops[3])=='Free':
                entry['Vj'] = 'Regs[{}]'.format(ops[3])
                entry['Qj'] = None
            else:
                entry['Qj'] = register_file.check_reg_state(ops[3])
                entry['Vj'] = None

            if entry_name == 'Load':
                entry['Vk'] = None
                entry['Qk'] = None
                register_file.set_registers(ops[1], entry['Name'])
            elif entry_name == 'Store':
                if register_file.check_reg_state(ops[3])=='Free':
                    entry['Vk'] = 'Regs[{}]'.format(ops[3])
                    entry['Qk'] = None
                else:
                    entry['Qk'] = register_file.check_reg_state(ops[3])
                    entry['Vk'] = None
        elif entry_name == 'Add' or entry_name == 'Mult':
            if register_file.check_reg_state(ops[2])=='Free':
                entry['Vj'] = 'Regs[{}]'.format(ops[2])
                entry['Qj'] = None
            else:
                entry['Qj'] = register_file.check_reg_state(ops[2])
                entry['Vj'] = None

            if register_file.check_reg_state(ops[3])=='Free':
                entry['Vk'] = 'Regs[{}]'.format(ops[3])
                entry['Qk'] = None
            else:
                entry['Qk'] = register_file.check_reg_state(ops[3])
                entry['Vk'] = None
            register_file.set_registers(ops[1], entry['Name'])
        entry['State'] = 'Issue'
        
    def store_cdb(self, data):
        for unit in self.entries.values():
            if unit == 'Store':
                for entry in unit:
                    if entry['State'] == 'Execute' and entry['Qk'] == None:
                        self.memory_unit.Mem[entry['A']] = entry['Vk']
                        entry['State'] = 'MemoryAccess'
                        entry['Busy'] = False
            else:
                for entry in unit:
                    if entry['Name'] == data['Dest']:
                        entry['Busy'] = False
                        entry['State'] = 'WriteResult'


    def write_result(self, data):
        # print(data)
        for unit in self.entries.values():

            for entry in unit:
                if entry['Qj'] == data['Dest']:
                    entry['Vj'] = data['Value']
                    entry['Qj'] = None
                if entry['Qk'] == data['Dest']:
                    entry['Vk'] = data['Value']
                    entry['Qk'] = None


    def show(self):
        # reload(sys)
        # sys.setdefaultencoding('utf8')

        head = ['Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'A', 'State']
        table = PrettyTable(head)

        for unit in self.entries.values():
            for entry in unit:
                ent = []
                for title in head:
                    ent.append(str(entry[title]))
                table.add_row(ent)

        print(table)
        return str(table)



if __name__ == '__main__':
    rvs = ReservationStation()
    # print(rvs.entries)
    rvs.show()
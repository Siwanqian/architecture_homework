from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，两个乘除保留站，2个整数单元，2个ld单元和2个sd单元
        self.entries = {
            'Load':[
                {'Name': 'Load{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,3)
            ],
            'Add':[
                {'Name': 'Add{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,4)
            ],
            'Mult':[
                {'Name': 'Mult{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,3)
            ],
            'Store':[
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,3)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,3)
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
    
    def execute(self, rob, cdb: CDB):
        for unit in self.entries.values():
            for entry in unit:
                # TODO：这个地方需要判断他是不是在发射阶段吗
                exec_unit = None
                if not entry['Busy']:
                    continue
                if self.check_dict[entry['Op']] == 'Add':
                    if entry['Busy'] and entry['Qj']==None and entry['Qk']==None and rob.get_state(entry['Dest']) == 'Issue':
                        exec_unit = self.fp_adder
                    else:
                        continue
                elif self.check_dict[entry['Op']] == 'Mult':
                    if entry['Busy'] and entry['Qj']==None and entry['Qk']==None and rob.get_state(entry['Dest']) == 'Issue':
                        exec_unit = self.fp_multipliers
                    else:
                        continue
                elif self.check_dict[entry['Op']] == 'Load' or self.check_dict[entry['Op']] == 'Store':
                    if not entry['Busy'] or entry['Qj']!=None:
                        continue
                    if rob.get_state(entry['Dest']) == 'Issue':
                        exec_unit = self.address_unit
                    elif rob.get_state(entry['Dest']) == 'Execute' and self.check_dict[entry['Op']] == 'Load':
                        exec_unit = self.memory_unit
                    else:
                        continue
                elif entry['Op'] in self.check_dict:
                    continue
                else:
                    raise ValueError('{}功能单元未定义'.format(entry['Op']))

                if not exec_unit.is_busy():
                    if self.check_dict[entry['Op']] == 'Load':
                        if rob.get_state(entry['Dest']) == 'Issue':
                            exec_unit.issue_instruction(entry['A'], entry['Vj'], entry)
                        elif rob.get_state(entry['Dest']) == 'Execute':
                            exec_unit.issue_instruction(entry['A'], entry['Dest'])
                    elif self.check_dict[entry['Op']] == 'Store':
                        exec_unit.issue_instruction(entry['A'], entry['Vj'], entry['Dest'])
                    else:
                        exec_unit.issue_instruction(entry['Op'], entry['Vj'], entry['Vk'], entry['Dest'])


        self.fp_adder.execute(cdb, rob)
        self.fp_multipliers.execute(cdb, rob)
        self.address_unit.execute(rob)
        self.integer_unit.execute(cdb, rob)
        self.memory_unit.execute(cdb, rob)
    def set_station(self, register_file: RegisterFile, ops: list, index: str, rob):
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
        entry['Dest'] = index

        j_value = None
        k_value = None
        if entry_name == 'Load': # ld x2,0(x1)
            entry['A'] = ops[2]
            j_value = ops[3]
        elif entry_name == 'Store': # sd x2,0(x1)
            entry['A'] = ops[2]
            j_value = ops[3]
            k_value = ops[1]
        elif entry_name == 'Add' or entry_name == 'Mult':
            entry['A'] = None
            j_value = ops[2]
            k_value = ops[3]
        elif entry_name == 'Int': # addi x2,x2,1
            entry['A'] = ops[3]
            j_value = ops[2]


        if register_file.check_reg_state(j_value)=='Free':
            entry['Vj'] = 'Regs[{}]'.format(j_value)
            entry['Qj'] = None
        else:
            reorder =  register_file.check_reg_state(j_value)
            value = rob.check_dest_state(reorder)
            if value == 'NotReady':
                entry['Qj'] = reorder
                entry['Vj'] = None
            else:
                entry['Vj'] = value
                entry['Qj'] = None
        
        if k_value != None:
            if register_file.check_reg_state(k_value)=='Free':
                entry['Vk'] = 'Regs[{}]'.format(k_value)
                entry['Qk'] = None
            else:
                reorder =  register_file.check_reg_state(k_value)
                value = rob.check_dest_state(reorder)
                if value == 'NotReady':
                    entry['Qk'] = reorder
                    entry['Vk'] = None
                else:
                    entry['Vk'] = value
                    entry['Qk'] = None

                    
    def write_result(self, data):
        for unit in self.entries.values():
            for entry in unit:
                if not entry['Busy']:
                    continue
                if entry['Dest'] == data['Dest']:
                    entry['Busy'] = False
                    continue
                if entry['Qj'] == data['Dest']:
                    entry['Vj'] = data['Value']
                    entry['Qj'] = None
                if entry['Qk'] == data['Dest']:
                    entry['Vk'] = data['Value']
                    entry['Qk'] = None


    def show(self):
        # reload(sys)
        # sys.setdefaultencoding('utf8')

        head = ['Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'Dest', 'A']
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
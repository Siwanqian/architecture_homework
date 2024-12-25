from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，两个乘除保留站，2个整数单元，2个ld单元和2个sd单元
        self.entries = {
            'Load':[
                {'Name': 'Load{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,6)
            ],
            'Add':[
                {'Name': 'Add{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,4)
            ],
            'Mult':[
                {'Name': 'Mult{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,3)
            ],
            'Store':[
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,4)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None} for i in range(1,6)
            ]
        }
        self.check_dict = {
            'fld': 'Load', 'ld': 'Load', 'fadd.d': 'Add', 'addi': 'Int', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Store', 'bne': 'Int'
        }
        self.fp_adder = FPAdder()
        self.fp_multipliers = FPMultiplier()
        self.address_unit = AddressUnit()
        self.memory_unit = MemoryUnit()
        self.integer_unit = IntegerUnit()
        

    def is_full(self, op: str):
        if op not in self.check_dict:
            raise ValueError('保留站类is_full函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]
        for entry in self.entries[entry_name]:
            if entry['Busy'] == False:
                return False
        return True
    
    """def get_empty_unit(self):
        empty_unit = []
        for unit_name, unit in self.entries.items():
            for entry in unit:
                if entry['Busy'] == False:
                    empty_unit.append(unit_name)
                    break
        return empty_unit"""


    def execute(self, rob, cdb: CDB):
        for unit in self.entries.values():
            for entry in unit:
                if not entry['Busy'] or entry['Qj']!=None:
                    continue

                exec_unit = None
                if self.check_dict[entry['Op']] == 'Add' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    exec_unit = self.fp_adder
                elif self.check_dict[entry['Op']] == 'Mult' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    exec_unit = self.fp_multipliers
                elif self.check_dict[entry['Op']] == 'Load' or self.check_dict[entry['Op']] == 'Store':
                    if rob.get_state(entry['Dest']) == 'Issue':
                        exec_unit = self.address_unit
                    elif rob.get_state(entry['Dest']) == 'Execute' and self.check_dict[entry['Op']] == 'Load':
                        exec_unit = self.memory_unit
                    else:
                        continue
                elif self.check_dict[entry['Op']] == 'Int' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    exec_unit = self.integer_unit
                elif entry['Op'] not in self.check_dict:
                    raise ValueError('{}功能单元未定义'.format(entry['Op']))
                else:
                    continue

                # 把ROB改成执行
                if not exec_unit.is_busy():                    
                    if self.check_dict[entry['Op']] == 'Load':
                        if rob.get_state(entry['Dest']) == 'Issue':
                            exec_unit.issue_instruction(entry['A'], entry['Vj'], entry)
                        elif rob.get_state(entry['Dest']) == 'Execute' :
                            exec_unit.issue_instruction(entry['A'], entry['Dest'])
                    elif  self.check_dict[entry['Op']] == 'Store':
                        exec_unit.issue_instruction(entry['A'], entry['Vj'], entry)
                    else:
                        exec_unit.issue_instruction(entry['Op'], entry['Vj'], entry['Vk'], entry['Dest'])
        self.fp_adder.execute(cdb, rob)
        self.fp_multipliers.execute(cdb, rob)
        self.address_unit.execute(rob)
        self.integer_unit.execute(cdb, rob)
        self.memory_unit.execute(cdb, rob)

    def set_station(self, register_file: RegisterFile, issue_bundle: tuple, rob, dependece: dict, rob_entries: list):
        for i, ops in enumerate(issue_bundle):
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
            
            # 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None
            # 第二条指令
            # ld指令：分析op[3]与上一条
            # sd指令：分析op[1]和op[3]的关联
            # alu：分析op[2]、op[3]的关联
            entry['Busy'] = True
            entry['Op'] = op
            entry['Dest'] = str(rob_entries[i])
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
                if op == 'bne':
                    j_value = ops[1]
                    k_value = ops[2]
                else:
                    entry['Vk'] = int(ops[3])
                    j_value = ops[2]

            if j_value != None:
                if i == 1 and j_value in dependece:
                    entry['Qj'] = str(rob_entries[0])
                    entry['Vj'] = None
                elif register_file.check_reg_state(j_value) == 'Free':
                    entry['Vj'] = register_file.get_value(j_value)
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
                if i == 1 and k_value in dependece:
                    entry['Qk'] = str(rob_entries[0])
                    entry['Vk'] = None
                elif register_file.check_reg_state(k_value) == 'Free':
                    entry['Vk'] = register_file.get_value(j_value)
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
        # self.show()
        return
    
    def is_store_able(self, h: int):
        for unit_name, unit in self.entries.items():
            if unit_name != 'Store':
                continue
            for entry in unit:
                if str(h) == entry['Dest'] and entry['Qk'] == None:
                    return True
        return False


    def write_store_back(self, rob_entry: dict, h: int):
        for unit_name, unit in self.entries.items():
            if unit_name != 'Store':
                continue
            for entry in unit:
                if str(h) == entry['Dest'] and rob_entry!= None and entry['Qk'] == None:
                    rob_entry['Value'] = entry['Vk']
                    self.memory_unit.Mem[entry['A']] = rob_entry['Value']
                    return True
        return False
    

    def write_result(self, data_list: list):
        if data_list == None:
            return
        for unit in self.entries.values():
            for entry in unit:
                if not entry['Busy']:
                    continue
                for data in data_list:
                    if entry['Dest'] == data['Dest']:
                        entry['Busy'] = False
                        continue
                    if entry['Qj'] == data['Dest']:
                        entry['Vj'] = data['Value']
                        entry['Qj'] = None
                    if entry['Qk'] == data['Dest']:
                        entry['Vk'] = data['Value']
                        entry['Qk'] = None
        return



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
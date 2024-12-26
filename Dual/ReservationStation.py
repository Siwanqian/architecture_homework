from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB
import copy

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，两个乘除保留站，2个整数单元，2个ld单元和2个sd单元
        self.entries = {
            'Load':[
                {'Name': 'Load{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,3)
            ],
            'Add':[
                {'Name': 'Add{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,4)
            ],
            'Mult':[
                {'Name': 'Mult{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,3)
            ],
            'Store':[
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,4)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,6)
            ]
        }
        self.check_dict = {
            'fld': 'Load', 'ld': 'Load', 'fadd.d': 'Add', 'addi': 'Int', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Store', 'bne': 'Int'
        }
        self.old_entries = copy.deepcopy(self.entries)
        self.item = 1
        self.fp_adder = FPAdder()
        self.fp_multipliers = FPMultiplier()
        self.address_unit = AddressUnit()
        self.memory_unit = MemoryUnit()
        self.integer_unit = IntegerUnit()
        self.item = 1
        self.loop_item = []
        

    def is_full(self, op: str):
        if op not in self.check_dict:
            raise ValueError('保留站类is_full函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]
        for entry in self.old_entries[entry_name]:
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

    def change_state(self, dest: str, state: str):
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        for unit in self.entries.values():
            for entry in unit:
                if entry['Name'] == dest:
                    entry['State'] = state


    def execute(self, cdb: CDB):
        # 只允许执行bne及之前的内容
        # 4self.show()
        execute_item = self.item if self.loop_item==[] else self.loop_item[0]
        for unit_name, unit in self.old_entries.items():
            exec_unit = None
            exec_entry = None
            old_item = None
            for entry in unit:
                if not entry['Busy'] or entry['Qj']!=None or entry['Item'] > execute_item:
                    continue
                if self.check_dict[entry['Op']] == 'Add' and entry['State']=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.fp_adder
                        old_item = entry['Item']
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Mult' and entry['State']=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.fp_multipliers
                        old_item = entry['Item']
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Load':
                    if entry['State'] == 'Issue':
                        if exec_unit == None or old_item >= entry['Item']:
                            exec_unit = self.address_unit
                            old_item = entry['Item']
                            exec_entry = entry
                    elif entry['State'] == 'Execute':
                        if exec_unit == None or old_item >= entry['Item']:
                            exec_unit = self.memory_unit
                            old_item = entry['Item']
                            exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Store' and entry['State']=='Issue':
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.address_unit
                        old_item = entry['Item']
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Int' and entry['State']=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.integer_unit
                        old_item = entry['Item']
                        exec_entry = entry
                elif entry['Op'] not in self.check_dict:
                    raise ValueError('{}功能单元未定义'.format(entry['Op']))

                # 把ROB改成执行
            if exec_unit != None and not exec_unit.is_busy():
                if self.check_dict[exec_entry['Op']] == 'Load':
                    if exec_entry['State'] == 'Issue':
                        for new_entry in self.entries[unit_name]:
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                    elif exec_entry['State'] == 'Execute':
                        exec_unit.issue_instruction(exec_entry['A'], exec_entry['Name'])
                elif  self.check_dict[exec_entry['Op']] == 'Store':
                    for new_entry in self.entries[unit_name]:
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                else:
                    exec_unit.issue_instruction(exec_entry['Op'], exec_entry['Vj'], exec_entry['Vk'], exec_entry['Name'])
        
        self.fp_adder.execute(cdb, self)
        self.fp_multipliers.execute(cdb, self)
        self.address_unit.execute(self)
        self.integer_unit.execute(cdb, self)
        self.memory_unit.execute(cdb, self)

    def issue(self, issue_bundle: tuple, register_file: RegisterFile, cdb: CDB):
        bundle_size = len(issue_bundle)
        # 记录冲突信息
        dependence = {}
        
        if bundle_size == 2:
            # 作为第一条指令
            # ld指令：op[1]需要被分析
            # sd指令：没有需要被分析的
            # alu指令：op[1]
            # bne：op[1], op[2]（在执行完之前，所有的都不允许执行，bne执行完即写结果，然后下一个周期之后的指令都可以运行
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
            

        
        first_entry = None

        for i, ops in enumerate(issue_bundle):
            op = ops[0]
            if op not in self.check_dict:
                raise ValueError('保留站类set_station函数出现未定义操作{}'.format(op))

            entry_name = self.check_dict[op]
            
            entry = None
            for ent in self.old_entries[entry_name]:
                if ent['Busy'] == False:
                    entry_ = ent
                    break
            if entry_ == None:
                raise ValueError('保留站类issue函数{}类型条目已满'.format(entry_name))
            
            for ent in self.entries[entry_name]:
                if entry_['Name'] == ent['Name']:
                    entry = ent
                    break
            
            if i == 0:
                first_entry = entry['Name']
            # 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None
            # 第二条指令
            # ld指令：分析op[3]与上一条
            # sd指令：分析op[1]和op[3]的关联
            # alu：分析op[2]、op[3]的关联
            entry['Busy'] = True
            entry['Op'] = op
            entry['State'] = 'Issue'
            entry['Item'] = self.item
            if op == 'bne':
                self.loop_item.append(entry['Item'])
            self.item += 1

            cdb_data = cdb.get_data()
            dict_data = {}
            for data in cdb_data:
                dict_data[data['Dest']] = data['Value']
    
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
                if i == 1 and j_value in dependence:
                    entry['Qj'] = first_entry
                    entry['Vj'] = None
                elif register_file.check_reg_state(j_value) == 'Free':
                    entry['Vj'] = register_file.get_value(j_value)
                    entry['Qj'] = None
                else:
                    dest = register_file.check_reg_state(j_value)
                    if dest in dict_data:
                        entry['Vj'] = dict_data[dest]
                        entry['Qj'] = None
                    else:
                        entry['Qj'] = dest
                        entry['Vj'] = None


            if k_value != None:
                if i == 1 and k_value in dependence:
                    entry['Qk'] = first_entry
                    entry['Vk'] = None
                elif register_file.check_reg_state(k_value) == 'Free':
                    entry['Vk'] = register_file.get_value(j_value)
                    entry['Qk'] = None
                else:
                    dest = register_file.check_reg_state(k_value)
                    if dest in dict_data:
                        entry['Vk'] = dict_data[dest]
                        entry['Qk'] = None
                    else:
                        entry['Qk'] = dest
                        entry['Vk'] = None

            if ops[0] != 'sd' and ops[0] != 'bne':
                register_file.set_registers(ops[1], entry['Name']) 
            
        return
    
    def check_store(self):
        for entry in self.entries['Store']:
            if entry['State'] == 'Execute' and entry['Qk'] == None:
                self.memory_unit.Mem[entry['A']] = entry['Vk']
                entry['State'] = 'MemoryAccess'
                entry['Busy'] = False



    def write_result(self, data_list: list):
        # 如果是bne，判断能不能继续执行
        for unit in self.entries.values():
            for entry in unit:
                if not entry['Busy']:
                    continue
                for data in data_list:
                    if entry['Name'] == data['Dest']:
                        entry['Busy'] = False
                        entry['State'] = 'WriteResult'
                        if entry['Op'] == 'bne':
                            self.loop_item.pop(0)
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

        head = ['Item', 'Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'A', 'State']
        table = PrettyTable(head)

        for unit in self.entries.values():
            for entry in unit:
                ent = []
                for title in head:
                    ent.append(str(entry[title]))
                table.add_row(ent)

        print(table)
        return str(table)
    
    def recover_data(self):
        self.old_entries = copy.deepcopy(self.entries)



if __name__ == '__main__':
    rvs = ReservationStation()
    # print(rvs.entries)
    rvs.show()
    print(7 > None)
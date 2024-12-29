from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB
import copy

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，2个乘除保留站，5个整数单元，5个ld单元和3个sd单元
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
        self.old_entries = copy.deepcopy(self.entries) # 设置上一周期表项，每次读取上一周期表项并在本周期表项中更新
        self.fp_adder = FPAdder()
        self.fp_multipliers = FPMultiplier()
        self.address_unit = AddressUnit()
        self.memory_unit = MemoryUnit()
        self.integer_unit = IntegerUnit()
        self.item = 1
        self.loop_item = []
        

    def is_full(self, op: str): # 判断指令对应的保留站是否已满
        if op not in self.check_dict:
            raise ValueError('保留站类is_full函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]
        for entry in self.old_entries[entry_name]:
            if entry['Busy'] == False:
                return False
        return True
    

    def change_state(self, dest: str, state: str): # 更新表项的状态
        # 判断更新的状态是否合法
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        for unit in self.entries.values():
            for entry in unit:
                if entry['Name'] == dest:
                    entry['State'] = state


    def execute(self, cdb: CDB):
        # 检测最早发射的未完成执行的跳转指令的对应条目
        execute_item = self.item if self.loop_item==[] else self.loop_item[0]
        for unit_name, unit in self.old_entries.items(): # 由于同周期每个阶段都是同时执行的，因此此处需要读取上一个周期能够执行的数据
            exec_unit = None
            exec_unit1 = None
            exec_entry = None
            exec_entry1 = None
            old_item = None
            old_item1 = None
            for entry in unit:
                if not entry['Busy'] or entry['Qj']!=None or entry['Item'] > execute_item: # 如果表项没有条目或者没有准备好执行或者表项在未完成执行的跳转指令之后
                    continue
                if self.check_dict[entry['Op']] == 'Add' and entry['State']=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']: # 检测最早发射的表项执行
                        exec_unit = self.fp_adder
                        old_item = entry['Item'] # 记录此时准备发射的表项
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Mult' and entry['State']=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']: # 检测最早发射的表项执行
                        exec_unit = self.fp_multipliers
                        old_item = entry['Item'] # 记录此时准备发射的表项
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Load':
                    if entry['State'] == 'Issue':
                        if exec_unit == None or old_item >= entry['Item']:
                            exec_unit = self.address_unit # 发射到地址单元
                            old_item = entry['Item']
                            exec_entry = entry
                    elif entry['State'] == 'Execute': # 如果地址已经计算完成
                        if exec_unit1 == None or old_item1 >= entry['Item']:
                            exec_unit1 = self.memory_unit
                            old_item1 = entry['Item']
                            exec_entry1 = entry
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

            if exec_unit != None and not exec_unit.is_busy(): # 如果有表项可以执行且执行单元不忙碌
                # 发射到对应的单元进行执行
                if self.check_dict[exec_entry['Op']] == 'Load':
                    if exec_entry['State'] == 'Issue':
                        for new_entry in self.entries[unit_name]: # 对于地址单元发射，由于需要直接写入条目的A表项中，因此需要传入本周期的保留站
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                elif  self.check_dict[exec_entry['Op']] == 'Store':
                    for new_entry in self.entries[unit_name]: # 对于地址单元发射，由于需要直接写入条目的A表项中，因此需要传入本周期的保留站
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                else:
                    exec_unit.issue_instruction(exec_entry['Op'], exec_entry['Vj'], exec_entry['Vk'], exec_entry['Name'])
            
            if exec_unit1 != None and not exec_unit1.is_busy(): # 如果有表项可以执行且执行单元不忙碌
                    if exec_entry1['State'] == 'Execute':
                        exec_unit1.issue_instruction(exec_entry1['A'], exec_entry1['Name'])
             
        # 各执行单元进行执行
        self.fp_adder.execute(cdb, self)
        self.fp_multipliers.execute(cdb, self)
        self.address_unit.execute(self)
        self.integer_unit.execute(cdb, self)
        self.memory_unit.execute(cdb, self)

    def is_empty(self): # 检测保留站中是否为空
        for unit in self.old_entries.values():
            for entry in unit:
                if entry['Busy'] == True:
                    return False
        return True
    
    def issue(self, issue_bundle: tuple, register_file: RegisterFile, cdb: CDB):
        bundle_size = len(issue_bundle)
        # 记录数据依赖信息
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
                    if ops1[0]=='addi' or ops1[0] == 'fadd.d' or ops1[0]=='fsub.d' or ops1[0]=='fmul.d' or ops1[0]=='fdiv.d' or ops1[0]=='bne':
                        dependence[ops1[2]] = ops0[1]
                if ops1[3] == ops0[1]:
                    if ops1[0]=='ld' or ops1[0]=='sd'or ops1[0]=='addi' or ops1[0] == 'fadd.d' or ops1[0]=='fsub.d' or ops1[0]=='fmul.d' or ops1[0]=='fdiv.d':
                        dependence[ops1[3]] = ops0[1]
            

        
        first_entry = None

        for i, ops in enumerate(issue_bundle):
            op = ops[0]
            if op not in self.check_dict:
                raise ValueError('保留站类set_station函数出现未定义操作{}'.format(op))

            entry_name = self.check_dict[op]
            # 为新发射的指令分配条目
            # 由于所有指令都是都是执行的，因此只能分配上一周期空闲的条目，本周期刚写回的空闲条目无法分配
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
            # 对每个指令分情况讨论其j和k的对应寄存器
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

            # 为j寄存器赋值
            if j_value != None:
                if i == 1 and j_value in dependence: # 如果是双发射的第二条指令且和第一条指令存在依赖关系
                    entry['Qj'] = first_entry
                    entry['Vj'] = None
                elif register_file.check_reg_state(j_value) == 'Free': # 需要的寄存器没有被占用
                    entry['Vj'] = register_file.get_value(j_value)
                    entry['Qj'] = None
                else:  # 需要的寄存器被占用了
                    dest = register_file.check_reg_state(j_value)
                    if dest in dict_data: # 如果该值在本周期已经写回
                        entry['Vj'] = dict_data[dest]
                        entry['Qj'] = None
                    else: # 如果该值没有被写回
                        entry['Qj'] = dest
                        entry['Vj'] = None

            # 为k寄存器赋值
            if k_value != None:
                if i == 1 and k_value in dependence: # 如果是双发射的第二条指令且和第一条指令存在依赖关系
                    entry['Qk'] = first_entry
                    entry['Vk'] = None
                elif register_file.check_reg_state(k_value) == 'Free':# 需要的寄存器没有被占用
                    entry['Vk'] = register_file.get_value(j_value)
                    entry['Qk'] = None
                else: # 需要的寄存器被占用了
                    dest = register_file.check_reg_state(k_value)
                    if dest in dict_data: # 如果该值在本周期已经写回
                        entry['Vk'] = dict_data[dest]
                        entry['Qk'] = None
                    else: # 如果该值没有被写回
                        entry['Qk'] = dest
                        entry['Vk'] = None

            # 如果指令需要写寄存器，设置寄存器对应的保留站表项
            if ops[0] != 'sd' and ops[0] != 'bne':
                register_file.set_registers(ops[1], entry['Name']) 
            
        return
    
    def check_store(self): # 检测store保留站是否能够写入存储器
        for entry in self.entries['Store']:
            if entry['State'] == 'Execute' and entry['Qk'] == None:
                self.memory_unit.Mem[entry['A']] = entry['Vk']
                entry['State'] = 'MemoryAccess'
                entry['Busy'] = False



    def write_result(self, data_list: list): # 写回结果
        for unit in self.entries.values(): # 检测每一个功能单元
            for entry in unit:
                if not entry['Busy']:
                    continue
                for data in data_list:
                    if entry['Name'] == data['Dest']: # 如果写的是对应表项，则设置表项为不忙碌
                        entry['Busy'] = False
                        entry['State'] = 'WriteResult'
                        if entry['Op'] == 'bne': # 如果bne指令执行完成，则后面的指令可以进入执行阶段
                            self.loop_item.pop(0)
                    # 如果存在数据依赖，则可以写入
                    if entry['Qj'] == data['Dest']:
                        entry['Vj'] = data['Value']
                        entry['Qj'] = None
                    if entry['Qk'] == data['Dest']:
                        entry['Vk'] = data['Value']
                        entry['Qk'] = None
        return



    def show(self):
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
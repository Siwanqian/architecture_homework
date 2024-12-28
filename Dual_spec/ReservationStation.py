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
                {'Name': 'Load{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None, 'Item': None} for i in range(1,6)
            ],
            'Add':[
                {'Name': 'Add{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None, 'Item': None} for i in range(1,4)
            ],
            'Mult':[
                {'Name': 'Mult{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None, 'Item': None} for i in range(1,3)
            ],
            'Store':[
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None, 'Item': None} for i in range(1,4)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'Dest': None, 'A': None, 'Item': None} for i in range(1,6)
            ]
        }
        self.check_dict = {
            'fld': 'Load', 'ld': 'Load', 'fadd.d': 'Add', 'addi': 'Int', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Store', 'bne': 'Int'
        }
        self.old_entries = copy.deepcopy(self.entries) # 设置上一周期表项，每次读取上一周期表项并在本周期表项中更新
        self.item = 1
        self.fp_adder = FPAdder()
        self.fp_multipliers = FPMultiplier()
        self.address_unit = AddressUnit()
        self.memory_unit = MemoryUnit()
        self.integer_unit = IntegerUnit()
        

    def is_full(self, op: str): # 判断指令对应的保留站是否已满
        if op not in self.check_dict:
            raise ValueError('保留站类is_full函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]
        for entry in self.old_entries[entry_name]:
            if entry['Busy'] == False:
                return False
        return True

    def execute(self, rob, cdb: CDB):
        for unit_name, unit in self.old_entries.items(): # 由于同周期每个阶段都是同时执行的，因此此处需要读取上一个周期能够执行的数据
            exec_unit = None
            exec_entry = None
            old_item = None
            for entry in unit:
                if not entry['Busy'] or entry['Qj']!=None: # 如果表项没有条目或者没有准备好执行
                    continue
                if self.check_dict[entry['Op']] == 'Add' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']: # 检测最早发射的表项执行
                        exec_unit = self.fp_adder
                        old_item = entry['Item'] # 记录此时准备发射的表项
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Mult' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']: # 检测最早发射的表项执行
                        exec_unit = self.fp_multipliers
                        old_item = entry['Item'] # 记录此时准备发射的表项
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Load':
                    if rob.get_state(entry['Dest']) == 'Issue': #
                        if exec_unit == None or old_item >= entry['Item']:
                            exec_unit = self.address_unit  # 发射到地址单元
                            old_item = entry['Item'] 
                            exec_entry = entry
                    elif rob.get_state(entry['Dest']) == 'Execute': # 如果地址已经计算完成
                        if exec_unit == None or old_item >= entry['Item']:
                            exec_unit = self.memory_unit # 发射到存储器单元
                            old_item = entry['Item']
                            exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Store' and rob.get_state(entry['Dest'])=='Issue':
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.address_unit
                        old_item = entry['Item']
                        exec_entry = entry
                elif self.check_dict[entry['Op']] == 'Int' and rob.get_state(entry['Dest'])=='Issue' and entry['Qk']==None:
                    if exec_unit == None or old_item >= entry['Item']:
                        exec_unit = self.integer_unit
                        old_item = entry['Item']
                        exec_entry = entry
                elif entry['Op'] not in self.check_dict:
                    raise ValueError('{}功能单元未定义'.format(entry['Op']))

            if exec_unit != None and not exec_unit.is_busy(): # 如果有表项可以执行且执行单元不忙碌
                # 发射到对应的单元进行执行
                if self.check_dict[exec_entry['Op']] == 'Load':
                    if rob.get_state(exec_entry['Dest']) == 'Issue':
                        for new_entry in self.entries[unit_name]: # 对于地址单元发射，由于需要直接写入条目的A表项中，因此需要传入本周期的保留站
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                    elif rob.get_state(exec_entry['Dest']) == 'Execute' :
                        exec_unit.issue_instruction(exec_entry['A'], exec_entry['Dest'])
                elif  self.check_dict[exec_entry['Op']] == 'Store':
                    for new_entry in self.entries[unit_name]: # 对于地址单元发射，由于需要直接写入条目的A表项中，因此需要传入本周期的保留站
                            if new_entry['Name'] == exec_entry['Name']:
                                exec_unit.issue_instruction(exec_entry['A'], exec_entry['Vj'], new_entry)
                else:
                    exec_unit.issue_instruction(exec_entry['Op'], exec_entry['Vj'], exec_entry['Vk'], exec_entry['Dest'])
        # 各执行单元进行执行
        self.fp_adder.execute(cdb, rob)
        self.fp_multipliers.execute(cdb, rob)
        self.address_unit.execute(rob)
        self.integer_unit.execute(cdb, rob)
        self.memory_unit.execute(cdb, rob)

    def set_station(self, register_file: RegisterFile, issue_bundle: tuple, rob, dependece: dict, rob_entries: list, cdb: CDB):
        # 为发射包中的指令分配ROB 
        for i, ops in enumerate(issue_bundle):
            op = ops[0]
            if op not in self.check_dict:
                raise ValueError('保留站类set_station函数出现未定义操作{}'.format(op))

            entry_name = self.check_dict[op]

            # 为新发射的指令分配条目
            # 由于所有指令都是都是执行的，因此只能分配上一周期空闲的条目，本周期刚写回的空闲条目无法分配
            entry_ = None
            for ent in self.old_entries[entry_name]:
                if ent['Busy'] == False:
                    entry_ = ent
                    break
            if entry_ == None:
                raise ValueError('保留站类set_station函数{}类型条目已满'.format(entry_name))
            
            for ent in self.entries[entry_name]:
                if entry_['Name'] == ent['Name']:
                    entry = ent
                    break

            entry['Busy'] = True
            entry['Op'] = op
            entry['Dest'] = str(rob_entries[i])
            entry['Item'] = self.item
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
                if i == 1 and j_value in dependece: # 如果是双发射的第二条指令且和第一条指令存在依赖关系
                    entry['Qj'] = str(rob_entries[0])
                    entry['Vj'] = None
                elif register_file.check_reg_state(j_value) == 'Free': # 需要的寄存器没有被占用
                    entry['Vj'] = register_file.get_value(j_value)
                    entry['Qj'] = None
                else: # 需要的寄存器被占用了
                    reorder =  register_file.check_reg_state(j_value) 
                    value = rob.check_dest_state(reorder)
                    if reorder in dict_data: # 如果该值在本周期已经写回
                        entry['Vj'] = dict_data[reorder]
                        entry['Qj'] = None
                    elif value == 'NotReady': # 如果该值没有被写回
                        entry['Qj'] = reorder
                        entry['Vj'] = None
                    else: # 在之前的周期已经被写回
                        entry['Vj'] = value
                        entry['Qj'] = None

            # 为k寄存器赋值
            if k_value != None:
                if i == 1 and k_value in dependece: # 如果是双发射的第二条指令且和第一条指令存在依赖关系
                    entry['Qk'] = str(rob_entries[0])
                    entry['Vk'] = None
                elif register_file.check_reg_state(k_value) == 'Free': # 需要的寄存器没有被占用
                    entry['Vk'] = register_file.get_value(j_value)
                    entry['Qk'] = None
                else: # 需要的寄存器被占用了
                    reorder =  register_file.check_reg_state(k_value)
                    value = rob.check_dest_state(reorder)
                    if reorder in dict_data: # 如果该值在本周期已经写回
                        entry['Vk'] = dict_data[reorder]
                        entry['Qk'] = None
                    elif value == 'NotReady': # 如果该值没有被写回
                        entry['Qk'] = reorder
                        entry['Vk'] = None
                    else: # 在之前的周期已经被写回
                        entry['Vk'] = value
                        entry['Qk'] = None
        return
    
    def is_store_able(self, h: int): # 检查存储指令是否可以提交
        for entry in self.old_entries['Store']:
            if str(h) == entry['Dest'] and entry['Qk'] == None:
                return True
        return False


    def write_store_back(self, rob_entry: dict, h: int): # 将需要存储的值写入存储器中
        for entry in self.old_entries['Store']:
            if str(h) == entry['Dest'] and rob_entry!= None and entry['Qk'] == None:
                rob_entry['Value'] = entry['Vk']
                self.memory_unit.Mem[entry['A']] = rob_entry['Value']
                return True
        return False
    

    def write_result(self, data_list: list): # 写回结果
        if data_list == None:
            return
        for unit in self.entries.values(): # 检测每一个功能单元
            for entry in unit:
                if not entry['Busy']:
                    continue
                for data in data_list:
                    if entry['Dest'] == data['Dest']: # 如果写的是对应表项，则设置表项为不忙碌
                        entry['Busy'] = False
                        continue
                    # 如果存在数据依赖，则可以写入
                    if entry['Qj'] == data['Dest']:
                        entry['Vj'] = data['Value']
                        entry['Qj'] = None
                    if entry['Qk'] == data['Dest']:
                        entry['Vk'] = data['Value']
                        entry['Qk'] = None
        return

    def recover_data(self): # 每周期最后更新表项，将旧表项中的值更新
        self.old_entries = copy.deepcopy(self.entries)


    def show(self):
        head = ['Name', 'Busy', 'Op', 'Vj', 'Vk', 'Qj', 'Qk', 'Dest', 'A', 'Item']
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
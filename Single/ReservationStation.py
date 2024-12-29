from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB
import re

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
                {'Name': 'Store{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,3)
            ],
            'Int':[
                {'Name': 'Int{}'.format(i), 'Busy': False, 'Op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'A': None, 'State': None, 'Item': None} for i in range(1,3)
            ]
        }
        self.check_dict = {
            'fld': 'Load', 'ld': 'Load', 'fadd.d': 'Add', 'addi': 'Add', 'fsub.d': 'Add', 'fmul.d': 'Mult', 'fdiv.d': 'Mult', 'sd': 'Store', 'bne': 'Int'
        }
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
        for entry in self.entries[entry_name]:
            if entry['Busy'] == False:
                return False
        return True
    
    def is_empty(self): # 检测保留站中是否为空
        for unit in self.entries.values():
            for entry in unit:
                if entry['Busy'] == True:
                    return False
        return True
    
    def execute(self, cdb: CDB):
        execute_item = self.item if self.loop_item==[] else self.loop_item[0]
        for unit_name, unit in self.entries.items(): # 由于同周期每个阶段都是同时执行的，因此此处需要读取上一个周期能够执行的数据
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


    def change_state(self, dest: str, state: str):  # 更新表项的状态
        if state not in ['Issue', 'Execute', 'WriteResult', 'MemoryAccess', 'Commit']:
            raise ValueError('无法改变至非法状态{}'.format(state))
        for unit in self.entries.values():
            for entry in unit:
                if entry['Name'] == dest:
                    entry['State'] = state

    def issue(self, ops: list, register_file: RegisterFile):
        op = ops[0]
        if op not in self.check_dict:
            raise ValueError('保留站类set_station函数出现未定义操作{}'.format(op))
        
        entry_name = self.check_dict[op]

        entry = None
        # 为新发射的指令分配条目
        for ent in self.entries[entry_name]:
            if ent['Busy'] == False:
                entry = ent
                break
        if entry == None:
            raise ValueError('保留站类set_station函数{}类型条目已满'.format(entry_name))    
        
        entry['Busy'] = True
        entry['Op'] = op
        entry['State'] = 'Issue'
        entry['Item'] = self.item
        if op == 'bne':
            self.loop_item.append(entry['Item'])
        self.item += 1
        # ld x2,0(x1)
        # sd x2,0(x1)
        # 对每个指令分情况讨论记录需要读的对应寄存器是否可用
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
        
        return
        
    def store_cdb(self, data): # 暂时缓存CDB中的数据
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


    def write_result(self, data): # 写回结果
        # print(data)
        for unit in self.entries.values(): # 检测每一个功能单元
            for entry in unit:
                # 如果存在数据依赖，则写入数据
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
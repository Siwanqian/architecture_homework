from RegisterFile import RegisterFile
from ExecUnit import FPAdder, FPMultiplier, AddressUnit, MemoryUnit, IntegerUnit
from prettytable import PrettyTable
from CDB import CDB

class ReservationStation:
    def __init__(self):
        # 3个浮点加法保留站，2个乘除保留站，5个整数单元，5个ld单元和3个sd单元
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
        

    def is_full(self, instruction: str): # 判断指令对应的保留站是否已满
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
                exec_unit = None
                if not entry['Busy']: # 如果表项没有条目则跳过
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

                if not exec_unit.is_busy(): # 如果有表项可以执行且执行单元不忙碌
                    # 发射到对应的单元进行执行
                    if self.check_dict[entry['Op']] == 'Load':
                        if rob.get_state(entry['Dest']) == 'Issue':
                            exec_unit.issue_instruction(entry['A'], entry['Vj'], entry)
                        elif rob.get_state(entry['Dest']) == 'Execute':
                            exec_unit.issue_instruction(entry['A'], entry['Dest'])
                    elif self.check_dict[entry['Op']] == 'Store':
                        exec_unit.issue_instruction(entry['A'], entry['Vj'], entry['Dest'])
                    else:
                        exec_unit.issue_instruction(entry['Op'], entry['Vj'], entry['Vk'], entry['Dest'])
        # 各执行单元进行执行
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
        # 分配保留站
        for ent in self.entries[entry_name]:
            if ent['Busy'] == False:
                entry = ent
                break
        if entry == None:
            raise ValueError('保留站类set_station函数{}类型条目已满'.format(entry_name))    
        
        entry['Busy'] = True
        entry['Op'] = op
        entry['Dest'] = index

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
            entry['A'] = ops[3]
            j_value = ops[2]

        # 为j寄存器赋值
        if register_file.check_reg_state(j_value)=='Free':# 需要的寄存器没有被占用
            entry['Vj'] = 'Regs[{}]'.format(j_value)
            entry['Qj'] = None
        else:
            reorder =  register_file.check_reg_state(j_value)
            value = rob.check_dest_state(reorder)
            if value == 'NotReady': # 需要的寄存器被占用了
                entry['Qj'] = reorder
                entry['Vj'] = None
            else: # 在之前的周期已经被写回
                entry['Vj'] = value
                entry['Qj'] = None
        
        # 为k寄存器赋值
        if k_value != None:
            if register_file.check_reg_state(k_value)=='Free': # 需要的寄存器没有被占用
                entry['Vk'] = 'Regs[{}]'.format(k_value)
                entry['Qk'] = None
            else: # 需要的寄存器被占用了
                reorder =  register_file.check_reg_state(k_value)
                value = rob.check_dest_state(reorder)
                if value == 'NotReady': # 如果该值没有被写回
                    entry['Qk'] = reorder
                    entry['Vk'] = None
                else: # 在之前的周期已经被写回
                    entry['Vk'] = value
                    entry['Qk'] = None

                    
    def write_result(self, data): # 写回结果
        for unit in self.entries.values(): # 检测每一个功能单元
            for entry in unit:
                if not entry['Busy']:
                    continue
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
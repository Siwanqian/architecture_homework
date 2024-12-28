class CDB:
    def __init__(self):
        self.data = []

    
    def is_full(self): # 检查cdb是否还有空闲位置可以传输
        return len(self.data) >= 2
    
    def is_empty(self): # 检测cdb是否传递信息
        return len(self.data) <= 0
    
    def get_data(self): # 获取cdb传递的数据
        return self.data
    
    def broadcast(self, dest, value): # 将数据广播
        if len(self.data) < 2:
            self.data.append({'Dest': dest, 'Value': value})
    
    def clear(self): # 清空cdb线路
        self.data.clear()

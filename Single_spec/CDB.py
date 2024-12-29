class CDB:
    def __init__(self):
        self.data = {}
        self.busy = False
    
    def is_busy(self): # 检查cdb是否忙碌
        return self.busy
    
    def get_data(self): # 获取cdb传递的数据
        return self.data
    
    def broadcast(self, dest, value): # 将数据广播
        self.data = {
            'Dest': dest,
            'Value': value
        }
        self.busy = True
    
    def clear(self): # 清空cdb线路
        self.busy = False
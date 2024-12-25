class CDB:
    def __init__(self):
        self.data = {}
        self.busy = False
    
    def is_busy(self):
        return self.busy
    
    def get_data(self):
        return self.data
    
    def broadcast(self, dest, value):
        self.data = {
            'Dest': dest,
            'Value': value
        }
        self.busy = True
    
    def clear(self):
        self.busy = False
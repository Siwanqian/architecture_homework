class CDB:
    def __init__(self):
        self.data = []

    
    def is_full(self):
        return len(self.data) >= 2
    
    def is_empty(self):
        return len(self.data) <= 0
    
    def get_data(self):
        return self.data
    
    def broadcast(self, dest, value):
        if len(self.data) < 2:
            self.data.append({'Dest': dest, 'Value': value})
    
    def clear(self):
        self.data.clear()

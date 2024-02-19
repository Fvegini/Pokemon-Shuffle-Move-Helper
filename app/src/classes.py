class Pokemon():
    def __init__(self, name, disabled, stage_added):
        self.name = name
        self.disabled = disabled
        self.stage_added = stage_added
        
    def __repr__(self):
        return self.name
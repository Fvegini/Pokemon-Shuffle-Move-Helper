class ExecutionVariable:
    
    current_stage: str
    current_strategy: str
    
    def __init__(self):
        self.current_stage = ""
        self.current_strategy = ""
        self.has_modifications = True
        self.socket_mode = True
        

execution_variables = ExecutionVariable()
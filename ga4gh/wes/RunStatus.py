import enum


class RunStatus(enum.Enum):
    Running = 1
    Failed = -1
    NotStarted = 0
    Complete = 2
    Canceled = 3
    
    def encode(self):
        return self.name
    
    def decode(name):
        return RunStatus[name]

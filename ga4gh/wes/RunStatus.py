import enum


class RunStatus(enum.Enum):
    RUNNING = 1
    FAILED = -1
    NOT_STARTED = 0
    COMPLETE = 2
    CANCELED = 3
    
    def encode(self):
        return self.name
    
    def decode(name):
        return RunStatus[name]

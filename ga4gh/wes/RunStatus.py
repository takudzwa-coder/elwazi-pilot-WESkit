import enum


class RunStatus(enum.Enum):
    Unknown = 0
    Queued = 1
    Initializing = 2
    Running = 3
    Paused = 4
    Complete = 5
    Executor_Error = 6
    System_Error = 7
    Canceled = 8
    Canceling = 9
    
    def encode(self):
        return self.name
    
    def decode(name):
        return RunStatus[name]

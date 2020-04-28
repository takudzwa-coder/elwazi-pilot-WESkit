import enum


class RunStatus(enum.Enum):
    UNKNOWN = 0
    QUEUED = 1
    INITIALIZING = 2
    RUNNING = 3
    PAUSED = 4
    COMPLETE = 5
    EXECUTOR_ERROR = 6
    SYSTEM_ERROR = 7
    CANCELED = 8
    CANCELING = 9

    def encode(self):
        return self.name
    
    def decode(name):
        return RunStatus[name]

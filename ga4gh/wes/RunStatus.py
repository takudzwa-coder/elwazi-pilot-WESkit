import enum

class RunStatus(enum.Enum):
    Running = 1
    Failed = -1
    NotStarted = 0
    Complete = 2

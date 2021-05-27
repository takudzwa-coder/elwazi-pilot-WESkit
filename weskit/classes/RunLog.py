#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from typing import List, Dict

from attr import dataclass
import json as j

from weskit.classes.RunStatus import RunStatus


@dataclass
class RunLog:

    run_id: str
    request: Dict[str, str]
    state: RunStatus
    task_logs: List[str]
    outputs: List[str]
    user_id: str
    log: Dict[str, str]

    @classmethod
    def from_json(cls, json: str):
        d = j.loads(json)
        d["state"] = RunStatus.from_string(d["state"])
        return cls(**d)

    def to_json(self) -> str:
        return j.dumps(self.__dict__)

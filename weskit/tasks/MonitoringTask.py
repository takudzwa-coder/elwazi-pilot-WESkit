#  Copyright (c) 2022. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team
from __future__ import annotations

from abc import ABCMeta

from weskit.celery_app import celery_app
from weskit.tasks.BaseTask import BaseTask
from weskit.tasks.SubmissionTask import SubmissionTask


class MonitoringTask(BaseTask, metaclass=ABCMeta):

    def monitor(self):
        # 1. Get a list of all relevant (runs)
        #   - in non-terminal stage (i.e. not completed, terminally-failed, etc.)
        #   - maybe running in this worker container
        # 2. Does the run have executor process-id
        #   - yes
        #      a. retrieve current status
        #      b. if changed: update database
        #      c. else if terminal: collect results and update database
        #      d. else nothing
        #   - no
        #      a. try finding a matching process with the given information
        #      b. if found: Continue with "2->yes"
        #      c. else if not found: try to resubmit the task via SubmissionTask
        # 3. Done
        pass


# TODO Run this task every X minutes. Take X from the weskit.yaml.
@celery_app.task(base=SubmissionTask)
def monitor_workflows():
    pass
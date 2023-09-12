# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

import os
import json
import time
import uuid
from typing import Dict, Optional

import yaml

from weskit.classes.Run import Run
from weskit.classes.ProcessingStage import ProcessingStage
from weskit.utils import now


def get_mock_run(workflow_url,
                 workflow_type,
                 workflow_type_version,
                 workflow_engine_parameters=None,
                 tags=None,
                 user_id="test_id",
                 workflow_params=None):
    workflow_engine_parameters = {}\
        if workflow_engine_parameters is None\
        else workflow_engine_parameters
    data = {
        "id": uuid.uuid4(),
        "processing_stage": ProcessingStage.RUN_CREATED,
        "request_time": None,
        "user_id": user_id,
        "request": {
            "workflow_url": workflow_url,
            "workflow_type": workflow_type,
            "workflow_type_version": workflow_type_version,
            "workflow_params": {"text": "hello_world"}
            if workflow_params is None else workflow_params,
            "workflow_engine_parameters": workflow_engine_parameters
        },
        "execution_log": {},
        "task_logs": [],
        "outputs": {},
        "celery_task_id": None,
    }
    if tags is not None:
        data["request"]["tags"] = tags
    run = Run(**data)
    return run


def is_within_timeout(start_time, timeout=30) -> bool:
    return (time.time() - start_time) <= timeout


def assert_within_timeout(start_time, timeout=30):
    assert is_within_timeout(start_time, timeout), "Test timed out"


def get_workflow_data(snakefile, config, engine_params: Optional[Dict[str, str]] = None):
    engine_params = {} if engine_params is None else engine_params
    with open(config) as file:
        workflow_params = json.dumps(yaml.load(file, Loader=yaml.FullLoader))

    data = {
        "workflow_params": workflow_params,
        "workflow_type": "SMK",
        "workflow_type_version": "7.30.2",
        "workflow_url": snakefile,
        "workflow_engine_parameters": json.dumps(engine_params)
    }
    return data


def assert_stage_is_not_failed(stage: ProcessingStage):
    assert not stage.is_error, "Failing run stage '{}'".format(stage.name)


def test_now_has_no_nanoseconds():
    t = now().timestamp()   # time in POSIX format: float in microseconds
    assert t - int(t) < 1


def test_env_licences():
    """Check if all used packages have a weak copyleft
    or are only required during compilation"""
    conda_env = os.system(''.join(['cat $CONDA_PREFIX/conda-meta/*.json | jq ".name, .license" ',
                                   '| paste - - | sort -k 2 | grep -v BSD | grep -v MIT ',
                                   '| grep -v Apache | grep -v LGPL | grep -v GCC-exception ',
                                   '| grep -v "ISC" | grep -v "OFL" | grep -v "EPL-1.0" ',
                                   '| grep -vP "Zlib|zlib" | grep -v "Unlicense" | grep -v "TCL" ',
                                   '| grep -vP "Python|PSF" | grep -v "Public-Domain" ',
                                   '| grep -v "HPND" | grep -v "IJG" ',
                                   '| grep -v "Classpath-exception" | grep -v "bzip2-1.0.6" ',
                                   '| grep -v "Ubuntu Font" ',
                                   '| grep -v -e "libnsl" -e "binutils_impl_linux-64" ',
                                   '-e "ld_impl_linux-64" -e "_libgcc_mutex" -e "uwsgi" ',
                                   '-e "readline" -e "libgcc" -e "coreutils" -e "python-debian" ',
                                   '-e "curl" -e "freetype"']))  # nosec
    # libnsl, binutils_impl_linux-64, _libgcc_mutex are GCC dependencies

    pip_env = os.system(''.join(['pip-licenses | grep -v BSD   | grep -v MIT   | grep -v Apache  ',
                                 '| grep -v LGPL   | grep -v GCC-exception   | grep -v "ISC" ',
                                 '| grep -v "OFL"   | grep -v "EPL-1.0"   | grep -vP "Zlib|zlib" ',
                                 '| grep -v "Unlicense"   | grep -v "TCL" ',
                                 '| grep -vP "Python|PSF" | grep -v "Public-Domain" ',
                                 '| grep -v "HPND"   | grep -v "IJG" ',
                                 '| grep -v "Classpath-exception" | grep -v "bzip2-1.0.6" ',
                                 '| grep -v "Eclipse Public License v2.0" | grep -v "MPL 2.0" ',
                                 '| grep -v "Zope Public License" | grep -v -e "uWSGI" ',
                                 '-e "dataclasses" -e "python-debian"']))  # nosec
    # "dataclasses" is under Apache licence
    # 'https://github.com/ericvsmith/dataclasses/blob/master/LICENSE.txt'
    # Note uWGSI is GPL-2 (https://github.com/unbit/uwsgi/blob/master/LICENSE)
    # but allows unrestricted usage (except for modifying the code etc.).
    assert conda_env == 256 and pip_env == 0

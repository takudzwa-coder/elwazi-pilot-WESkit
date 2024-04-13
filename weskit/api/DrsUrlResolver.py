# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
import os
import re
import requests
from copy import deepcopy
from json import JSONDecodeError
from os.path import normpath, commonprefix
from pathlib import Path
from typing import List, Optional, Dict, Callable, TypeVar, Union, Any
from urllib.parse import urlparse

from werkzeug.datastructures import FileStorage, ImmutableMultiDict

logger = logging.Logger(__file__)



def drsUrlResolver(data):
    parse_result = json.loads(data["workflow_params"])
    for param in parse_result:
        input_objs = []
        for input_obj in parse_result[param].split():
            parsed_url = urlparse(input_obj)

            if parsed_url.scheme != "drs":
                input_objs.append(input_obj)
            else:

                ##drs object url
                drs_hostname = parsed_url.hostname
                drs_port = parsed_url.port
                drs_id = parsed_url.path
                drs_objects_path ="objects"
                ga4gh_drs_base_url = "http://" + drs_hostname + ":{}/ga4gh/{}/v1/{}"
                drs_object_url = ga4gh_drs_base_url.format(drs_port,"drs", drs_objects_path)
                http_method = "GET"
                request_url = drs_object_url + drs_id


                drs_obj = requests.request(http_method, request_url)
                if drs_hostname in ['localhost', '127.0.0.1']:
                    access_methods = drs_obj.json()["access_methods"][0]
                    file_path = access_methods["access_url"]["url"]
                    input_objs.append(file_path)

                else:
                    access_methods = drs_obj.json()["access_methods"][1]
                    file_access_id = access_methods["access_id"]
                    drs_streaming_path = "stream"
                    drs_streaming_url = ga4gh_drs_base_url.format(drs_port,"drs", drs_streaming_path) + drs_id + "/" +file_access_id
                    input_objs.append(drs_streaming_url)
        parse_result[param] = " ".join(input_objs)
    data["workflow_params"] = json.dumps(parse_result)
    return data


    
# drsUrlResolver()
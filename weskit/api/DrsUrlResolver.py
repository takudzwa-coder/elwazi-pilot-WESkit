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



def drsUrlRersover(data):
    parse_result = json.loads(data["workflow_params"])
               
    parsed_url = urlparse(parse_result['input'])
    if parsed_url.scheme != "drs":
        return data
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
    print(drs_obj.json())
    print("hostname", drs_hostname)
    if drs_hostname in ['localhost', '127.0.0.1']:
        access_methods = drs_obj.json()["access_methods"][0]
        file_path = access_methods["access_url"]["url"]
        # parse_result["input"] = file_path
        # data["workflow_params"] = parse_result
        data["workflow_params"] = "{\"input\":\"" + file_path + "\"}"
       
    else:
        access_methods = drs_obj.json()["access_methods"][1]
        file_access_id = access_methods["access_id"]
        drs_streaming_path = "stream"
        drs_streaming_url = ga4gh_drs_base_url.format(drs_port,"drs", drs_streaming_path) + drs_id + "/" +file_access_id
        # parse_result["input"] = drs_streaming_url
        # data["workflow_params"] = parse_result
        data["workflow_params"] = "{\"input\":\"" + drs_streaming_url + "\"}"
    return data

    
# drsUrlRersover()

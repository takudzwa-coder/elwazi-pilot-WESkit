# SPDX-FileCopyrightText: 2023 The WESkit Contributors
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import logging
import os
import socket
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
        if isinstance(parse_result[param], list): ##include function for list json files
            print("skipping json list") 
        else:
            for input_obj in parse_result[param].split():
                parsed_url = urlparse(input_obj)

                if parsed_url.scheme != "drs":
                    input_objs.append(input_obj)
                else:

                    ##drs object url
                    drs_hostname = parsed_url.hostname
                    drs_port = parsed_url.port or 443 # Default to 443 if no port is specified
                    drs_id = parsed_url.path
                    drs_objects_path ="objects"
                    # ga4gh_drs_base_url = "http://" + drs_hostname + ":{}/ga4gh/{}/v1/{}"
                    ga4gh_drs_base_url = drs_hostname + ":{}/ga4gh/{}/v1/{}"
                    drs_object_url = ga4gh_drs_base_url.format(drs_port,"drs", drs_objects_path)
                    http_method = "GET"
                    request_url = drs_object_url + drs_id
                    
                    print("DRS URL: ", request_url)


                    
                    if drs_hostname in ['localhost', '127.0.0.1', socket.gethostbyname(socket.gethostname())]:
                        request_url = "http://" + request_url
                        print("Localhost DRS URL: ", request_url)
                        drs_obj = requests.request(http_method, request_url)
                        access_methods = drs_obj.json()["access_methods"]
                        access_url = access_methods[0]["access_url"]["url"]
                        input_objs.append(access_url)
                        
                    #special case for elwazi.omic.ai to get signed access URL    
                    elif drs_hostname == "elwazi.omics.ai":
                        
                        request_url = "https://"+ request_url + "/access/https"
                        print("Elwazi DRS URL: ", request_url)
                        drs_obj = requests.request(http_method, request_url)
                        access_url = drs_obj.json()["url"]
                        print("Access URL: ", access_url)
                        # input_objs.append(access_url)
                        #fromart  http special chars
                        # access_url = access_url.split("?")[0] + "%3F" + access_url.split("?")[1]
                        input_objs.append(access_url)

                    else:
                        request_url = "http://" + request_url
                        print("Remote Prem DRS URL: ", request_url)
                        drs_obj = requests.request(http_method, request_url)
                        access_methods = drs_obj.json()["access_methods"]
                        if access_methods[0]["type"] == 's3':
                            access_url = access_methods[0]["access_url"]["url"]
                            input_objs.append(access_url)
                        else:
                            print(access_methods)
                            file_access_id = access_methods[1]["access_id"]
                            drs_streaming_url = "http://" + ga4gh_drs_base_url.format(drs_port,"drs", "stream") + drs_id + "/" +file_access_id
                            input_objs.append(drs_streaming_url)
                        
            parse_result[param] = " ".join(input_objs)
    data["workflow_params"] = json.dumps(parse_result)
    return data



def url_omics():
    """
    This function is a placeholder for the URL omics functionality.
    It currently does not implement any logic but serves as a stub for future development.
    """
    pass
    
# drsUrlResolver()
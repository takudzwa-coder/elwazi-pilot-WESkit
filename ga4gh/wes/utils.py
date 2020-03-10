from random import choice
from datetime import datetime

def create_run_id():
    print("_create_run_id")
    # create run identifier
    charset = "0123456789abcdefghijklmnopqrstuvwxyz"
    length = 8
    run_id = "".join(choice(charset) for __ in range(length))
    return run_id

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
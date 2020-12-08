from datetime import datetime


def get_current_time():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

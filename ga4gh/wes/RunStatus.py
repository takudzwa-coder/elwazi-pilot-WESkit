import enum, os, yaml


class RunStatus(enum.Enum):
    Running = 1
    Failed = -1                                                                                                         # this status is not a part of the specification -> executor_error or system_error
    Unknown = 0                                                                                                         # NotStarted status is not part of the specification
    Complete = 2
    Canceled = -2
    
    def encode(self):
        return self.name
    
    def decode(name):
        return RunStatus[name]


def load_yaml():
    path = os.path.abspath(os.path.join("get_service_info.yaml"))
    with open(path, "r") as ff:
        file = yaml.load(ff, Loader=yaml.FullLoader)
    return file


def rewrite_yaml(file, rewrite_data):
    path = os.path.abspath(os.path.join("get_service_info.yaml"))
    with open(path, "w"):
        new_file = yaml.dump(file, rewrite_data)
    return new_file


def count_states_running_up():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["running"]
    counter = counter + 1
    rewrite_yaml(data, counter)


def count_states_running_down():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["running"]
    counter = counter - 1
    rewrite_yaml(data, counter)


def count_states_unknown_up():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["unknown"]
    counter = counter + 1
    rewrite_yaml(data, counter)


def count_states_unknown_down():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["unknown"]
    counter = counter - 1
    rewrite_yaml(data, counter)


def count_states_complete_up():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["complete"]
    counter = counter + 1
    rewrite_yaml(data, counter)


def count_states_complete_down():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["complete"]
    counter = counter - 1
    rewrite_yaml(data, counter)


def count_states_canceled_up():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["canceled"]
    counter = counter + 1
    rewrite_yaml(data, counter)


def count_states_canceled_down():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["canceled"]
    counter = counter - 1
    rewrite_yaml(data, counter)


def count_states_failed_up():
    data = load_yaml()
    counter = data["serviceInfo"]["system_state_counts"]["failed"]
    counter = counter + 1
    rewrite_yaml(data, counter)

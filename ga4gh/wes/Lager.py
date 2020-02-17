def store_run(self, run):
    collection_name = run
    datetime_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    exit_code = response
    db[collection_name].insert(
        {
            "run_id": run,
            "run_status": state,
            "request_time": datetime_now,
            "request": [{"workflow_params": workfow_parameters,
                         "workflow_url": workflow_url
                         }
                        ],
            "executed_command": command_name,
            "run_log": [{"start_time": start,
                         "end_time": end,
                         "cmd": None,
                         "exit_status": exit_code,
                         "standard_output": stdout,
                         "standard_error": stderr
                         }
                        ],
        }
    )
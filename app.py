#!/usr/bin/env python3

import connexion

app = connexion.App(__name__)
app.add_api("20191217_workflow_execution_service.swagger.yaml")
application = app.app

if __name__ == "__main__":
    app.run(port=8080, server="gevent")
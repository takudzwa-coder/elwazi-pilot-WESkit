#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

from weskit import create_database, create_celery
from weskit import create_app


def main():
    app = create_app(create_celery(),
                     create_database())
    app.run(host="127.0.0.1", port=5000)

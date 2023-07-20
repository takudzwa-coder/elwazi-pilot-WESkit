#  Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
#
#  Distributed under the MIT License. Full text at
#
#      https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
#
#  Authors: The WESkit Team

FROM registry.gitlab.com/one-touch-pipeline/weskit/api/base:master

EXPOSE 5000

# For development bind your weskit repository to /weskit. It needs to be readable by the
# USER_ID that is used here. You can for instance use your personal user and group IDs.
#
# For production, directly build the container with the correct repository version checked out.
# Use a user and group ID available on the deployment system.
WORKDIR /weskit

# The source code is changing more frequently. Copy it only in the outer layer of the container.
COPY ./ /weskit

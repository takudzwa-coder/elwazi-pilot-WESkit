#!/bin/bash
# This script generates self signed development certificates.
# Per default the certificates will be stored in the certs sub-folder.
# The path can be changed by setting command line arg 1
# It will not overwrite existing certificates

# localhost and hostname of the generating machine are valid dns names for the certificate!


if [ -z $1 ]; then 
    # Set path to here/certs
    certStoragePath=$(dirname $(readlink -f  "$0"))"/certs"

else path=$1;
fi
prefix=$certStoragePath"/weskit"

if [ ! -f $prefix".key" ] || [ ! -f $prefix".crt" ]; then
    echo "Least one certificate file missing / not found!"
    echo "Generating new certificate and write it to: "$certStoragePath".*"
    # Generate Self Signed Cert
    openssl req -x509 -newkey rsa:4096 -sha256 -days 30 -nodes -keyout $prefix.key -out $prefix.crt -subj "/CN=localhost" -addext "subjectAltName = DNS:localhost,DNS:keycloak,DNS:127.0.0.1,DNS:"$(hostname) 
    # Convert Certificate to PEM Format needed for requests from python
    openssl x509 -in $prefix.crt -out $prefix.pem -outform PEM
    exit 0
fi

echo "Using existing certificate!"



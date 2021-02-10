#!/bin/bash

if [ -z $1 ]; then 
path=$(dirname $(realpath $pwd$0))"/certs"

else path=$1;
fi
prefix=$path"/weskit"

if [ ! -f $prefix".key" ] || [ ! -f $prefix".crt" ]; then
    echo "Least one certificate file missing / not found!"
    echo "Generating new certificate and write it to: "$path".*"
    openssl genrsa -out $prefix".key" 4096
    openssl req -new -key $prefix".key" -out $prefix".csr" -batch
    openssl x509 -req -days 90 -in $prefix".csr" -signkey $prefix".key" -out $prefix".crt"
    exit 0
fi

echo "Using existing certificate!"



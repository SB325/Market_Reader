#!/bin/sh

kubectl create secret docker-registry <name-of-secret> \
  --docker-server=localhost:5050 \
  --docker-username=<DOCKER_USER> \
  --docker-password=<DOCKER_PASSWORD> \
  --docker-email=<DOCKER_EMAIL>

  kubectl create secret tls tls_certs --cert=<path/to/tls.crt> --key=<path/to/tls.key> --namespace=default

#!/bin/sh

# Filter only lines containing SECRET_VAR_A or SECRET_VAR_B
# grep -E '^(SECRET_VAR_A|SECRET_VAR_B)=' app.env > secret.env
grep -E '^(MY_DNS_NAME)=' ~/src/homeserver/.env > certs/hostname.env
grep -E '^(TLS_KEY_FILE|TLS_CERT_FILE)=' ~/src/homeserver/.env > certs/tls_certs.env
grep -E '^(PG_USER|PG_PASS)=' ~/src/homeserver/.env > credentials/pg_creds.env

## DOCKER SECRETS ##
kubectl create secret docker-registry <name-of-secret> \
  --docker-server=localhost:5050 \
  --docker-username=<DOCKER_USER> \
  --docker-password=<DOCKER_PASSWORD> \
  --docker-email=<DOCKER_EMAIL>

## POSTGRES SECRETS ##
# Admin/superuser credentials
kubectl create secret generic postgres-credentials \
  --from-env-file=credentials/pg_creds.env 

kubectl create secret tls tls_secrets --cert=<path/to/tls.crt> --key=<path/to/tls.key> --namespace=default

kubectl create secret generic hostname-secret --from-env-file=certs/hostname.env
kubectl create secret generic tls-secrets --from-env-file=certs/tls_certs.env
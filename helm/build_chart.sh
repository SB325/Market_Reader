#!/bin/sh

# Add External Secrets Operator to connect to AWS Secrets Manager
helm repo add external-secrets https://external-secrets.io
helm install external-secrets \
    external-secrets/external-secrets \
    --namespace external-secrets --create-namespace

helm dependency build

helm upgrade --install marketreader ./ \
  --set grafana.ingress.hosts[0]=${MY_DNS_NAME} \
  --set grafana.ingress.tls[0].hosts[0]=${MY_DNS_NAME} \
  --set marketreader.services.pgadmin.service.servicePort=80 \
  --set marketreader.services.pgadmin.service.ports.targetPort=${PGADMIN_PORT} \
  --set marketreader.ingress.hostGroups.host1.paths[0].servicePort=${PGADMIN_PORT} \
  --set marketreader.ingress.hostGroups.host1.paths[1].servicePort=${PGADMIN_PORT} \
  --set persistentVolumes.otel-data.path=${HOMESERVER_PATH}/telemetry/otel-config.yaml
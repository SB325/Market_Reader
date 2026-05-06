#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e
if [ -f "../../../.env" ]; then
    set -a
    source ../../../.env
    set +a
fi

# Default namespace. Change this if your Helm charts are elsewhere
NAMESPACE=${KUBERNETES_NAMESPACE}

# orig_dir = cd ../terraform/bootstrap
# terraform init
# # apply create_secure_s3.tf
# terraform apply -auto-approve

# cd orig_dir/../terraform/secrets
# # save tfstate to secure s3
# terraform apply -auto-approve

echo "============================================="
echo "  K3s / Helm Secret Generator"
echo "============================================="

# 1. Docker Image Registry Secret
echo -e "\n 1. Setting up Docker Registry Secret..."

kubectl create secret docker-registry registry-pull-secret \
  --docker-server="${DOCKER_REGISTRY_URL}" \
  --docker-username="${DOCKER_REGISTRY_USER}" \
  --docker-password="${DOCKER_REGISTRY_PASS}" \
  --docker-email="${DOCKER_REGISTRY_EMAIL}" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Ingress TLS Secret
echo -e "\n 2. Setting up Ingress TLS Secret..."

if [ ! -f "${TLS_CERT_FILE}" ] || [ ! -f "${TLS_KEY_FILE}" ]; then
    echo "Error: Certificate or Key file not found. Skipping TLS secret creation."
else
    kubectl create secret tls tls-secrets \
      --cert="${TLS_CERT_FILE}" \
      --key="${TLS_KEY_FILE}" \
      --namespace="${NAMESPACE}" \
      --dry-run=client -o yaml | kubectl apply -f -
fi

# Host Secret
kubectl create secret generic hostname-secret  \
    --from-literal=username="${PROXY_USER}" \
    --from-literal=password="${PROXY_PASSWORD}" \
    --namespace="${NAMESPACE}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Pgadmin Secret
kubectl create secret generic pgadmin-credentials  \
    --from-literal=pgadmin_email="${PGADMIN_EMAIL}" \
    --from-literal=pgadmin_pw="${PGADMIN_PW}" \
    --namespace="${NAMESPACE}" \
    --dry-run=client -o yaml | kubectl apply -f -

# 3. Postgres Password Secret
echo -e "\n 3. Setting up Postgres Secret..."

kubectl create secret generic postgres-credentials \
  --from-literal=postgres-password="${PG_PASS}" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Grafana Admin Secret
echo -e "\n 4. Setting up Grafana Admin Secret... "

kubectl create secret generic grafana-secret \
  --from-literal=admin-user="${GRAFANA_ADMIN_USER}" \
  --from-literal=admin-password="${GRAFANA_ADMIN_PASSWORD}" \
  --namespace="${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "\n All requested secrets successfully applied to namespace: ${NAMESPACE}"
kubectl get secrets -n "${NAMESPACE}" | grep -E "registry-pull-secret|ingress-gateway-tls|postgres-secret|grafana-secret"
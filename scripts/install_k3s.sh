#!/bin/sh

# install k3s
sudo curl -sfL https://get.k3s.io | sh -

# copy the kubeconfig file for k3s to your home directory:
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# set your KUBECONFIG environment variable to point to this file:
export KUBECONFIG=~/.kube/config/k3s.yaml

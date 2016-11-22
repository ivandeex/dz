#!/bin/bash
cd $(dirname $(readlink -f $0))
ansible-vault decrypt --output=secret.yml group_vars/all/vault.yml
chmod 600 secret.yml group_vars/all/vault.yml

#!/bin/bash
cd $(dirname $(readlink -f $0))
ansible-vault encrypt --output=group_vars/all/vault.yml secret.yml
chmod 600 group_vars/all/vault.yml secret.yml

#!/bin/bash
base_dir=$(dirname $(dirname $(readlink -f $0)))
cd $base_dir/ansible
encrypted=./group_vars/all/vault.yml
decrypted=../secrets.yml
if [ ! -r $encrypted ]; then
  echo "file not found: $(readlink -f $encrypted)"
  exit 1
fi
ansible-vault decrypt --output=$decrypted $encrypted
chmod 600 $encrypted $decrypted 2>/dev/null

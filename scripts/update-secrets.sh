#!/bin/bash
base_dir=$(dirname $(dirname $(readlink -f $0)))
cd $base_dir/ansible
encrypted=./group_vars/all/vault.yml
decrypted=../secrets.yml
if [ ! -r $decrypted ]; then
  echo "file not found: $decrypted"
  exit 1
fi
if [ $decrypted -nt $encrypted -o x"$1" = x"-f" -o x"$1" = x"--force" ]; then
  ansible-vault encrypt --output=$encrypted $decrypted
fi
chmod 600 $decrypted $encrypted 2>/dev/null

#!/bin/bash
cd $(dirname $(readlink -f $0))
test secret.yml -nt group_vars/all/vault.yml && ./update-secret.sh
ansible-playbook -i hosts task-prepare.yml
cd ..
python manage.py makemigrations --noinput --exit && python manage.py migrate --noinput
python manage.py collectstatic --noinput

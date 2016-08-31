#!/bin/bash
cd $(dirname $(readlink -f $0))
test secret.yml -nt group_vars/all/vault.yml && ./update-secret.sh
ansible-playbook -i hosts task-prepare.yml
cd ..
python manage.py makemigrations --noinput --exit && python manage.py migrate --noinput
python manage.py compilemessages
npm run assets
# post-processing disabled because whitenoise tries to load
# images included by css and fails on dz-base.css.
python manage.py collectstatic --no-input --no-post-process

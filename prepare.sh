#!/bin/bash
project_dir=$(dirname $(readlink -f $0))
cd $project_dir/ansible
test secret.yml -nt group_vars/all/vault.yml && ./update-secret.sh
ansible-playbook -i hosts task-prepare.yml
cd $project_dir
python manage.py makemigrations --noinput --exit && python manage.py migrate --noinput
python manage.py compilemessages
npm run makeprod
python manage.py collectstatic --noinput

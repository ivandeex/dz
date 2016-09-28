#!/bin/bash
project_dir=$(dirname $(readlink -f $0))

ansible_tasks()
{
  cd $project_dir/ansible
  [ ./secret.yml -nt ./group_vars/all/vault.yml ] && ./update-secret.sh
  ansible-playbook -i hosts task-prepare.yml
}

migrate_db()
{
  cd $project_dir
  python manage.py makemigrations --noinput --exit && \
    python manage.py migrate --noinput
}

make_messages()
{
  cd $project_dir/dz
  python ../manage.py makemessages -l en -l ru -l sl
}

compile_messages()
{
  cd $project_dir
  python manage.py compilemessages
}

prepare_prod()
{
  cd $project_dir
  npm run makeprod
  python manage.py collectstatic --noinput
}

case "$1" in
  lang)
    make_messages
    ;;
  full)
    ansible_tasks
    migrate_db
    compile_messages
    prepare_prod
    ;;
  devel)
    migrate_db
    compile_messages
    ;;
  *)
    echo "usage: $0 lang|full|devel"
esac

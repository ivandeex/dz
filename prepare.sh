#!/bin/bash
project_dir=$(dirname $(readlink -f $0))
cd $project_dir
[ -e .env ] && . .env

ansible_tasks()
{
  cd $project_dir/ansible
  [ ./secret.yml -nt ./group_vars/all/vault.yml ] && ./update-secret.sh
  ansible-playbook -i hosts task-prepare.yml
  cd $project_dir
}

migrate_db()
{
  python manage.py makemigrations --noinput --exit && \
    python manage.py migrate --noinput
}

make_messages()
{
  python ../manage.py makemessages -l en -l ru -l sl
}

compile_messages()
{
  python manage.py compilemessages
}

prepare_prod()
{
  npm run makeprod
  python manage.py collectstatic --noinput
}

case "$1" in
  lang)
    make_messages
    ;;
  devel)
    migrate_db
    compile_messages
    ;;
  prod)
    prepare_prod
    ;;
  all)
    ansible_tasks
    migrate_db
    compile_messages
    prepare_prod
    ;;
  *)
    echo "usage: $0 lang|devel|prod|all"
esac

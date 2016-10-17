#!/bin/bash
action="$1"
shift
extra_args="$*"

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

run_test()
{
  # We do not let django create testdatabase for security reasons.
  # Database is created manually by ansible, and here we supply the
  # `--keep` option telling django to skip creating and dropping.
  python manage.py check && \
  python manage.py test --keep --reverse --failfast --verbosity 2 $extra_args
}

run_lint()
{
  flake8 && \
  sass-lint -v -q && \
  eslint dz/assets webpack.config.babel.js
}

case "$action" in
  lang)
    make_messages
    ;;
  devel)
    migrate_db
    compile_messages
    ;;
  test)
    run_test
    ;;
  lint)
    run_lint
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
    echo "usage: $0 all|prod|devel|lang|test|lint"
esac

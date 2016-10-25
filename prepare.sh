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
  # Compile and bundle production javascript and css:
  npm run makeprod
  # Use `-v0` to silence verbose whitenoise messages:
  python manage.py collectstatic --noinput -v0
}

run_test()
{
  # We do not let django create test database for security reasons.
  # Database is created manually by ansible, and here we supply the
  # `--keep` option telling django to skip creating and dropping.
  python manage.py check && \
  python manage.py test --keep --reverse --failfast --verbosity 2 $extra_args
}

run_coverage()
{
  coverage run --source=. --omit='*/bot/*' manage.py test -k $extra_args
  coverage report
}

liveserver_test()
{
  TEST_LIVESERVER=1 python manage.py test --keep --liveserver=0.0.0.0:8000 --tag liveserver $extra_args
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
    npm run makedevel
    ;;
  test)
    run_test
    ;;
  coverage)
    run_coverage
    ;;
  lint)
    run_lint
    ;;
  liveserver)
    liveserver_test
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
    echo "usage: $0 all|prod|devel|lang|test|lint|coverage|liveserver"
esac

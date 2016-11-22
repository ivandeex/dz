#!/bin/bash
action="$1"
shift
extra_args="$*"

project_dir=$(dirname $(dirname $(readlink -f $0)))
cd $project_dir
[ -e .env ] && . .env

run_ansible()
{
  playbook="$1"
  cd ansible
  [ ./secret.yml -nt ./group_vars/all/vault.yml ] && ./update-secret.sh
  ansible-playbook $playbook.yml $extra_args
  cd ..
}

migrate_db()
{
  python manage.py makemigrations --noinput --exit && \
    python manage.py migrate --noinput
}

make_messages()
{
  cd dz
  python ../manage.py makemessages -l en -l ru -l sl
  cd ..
}

compile_messages()
{
  cd dz
  python ../manage.py compilemessages
  cd ..
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

run_linters()
{
  flake8 && \
  sass-lint -v -q && \
  eslint dz/assets webpack.config.babel.js
}

set -x
case "$action" in
  lang)
    make_messages
    ;;
  devel)
    pip -q install -r requirements/devel.txt
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
    run_linters
    ;;
  liveserver)
    liveserver_test
    ;;
  prod)
    prepare_prod
    ;;
  build-bot)
    run_ansible task-build-bot
    ;;
  all)
    run_ansible task-prepare
    migrate_db
    compile_messages
    prepare_prod
    ;;
  *)
    echo "usage: $0 {all prod devel lang build-bot test lint coverage liveserver}"
esac

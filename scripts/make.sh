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
  ./scripts/update-secrets.sh
  cd ansible
  ansible-playbook plays/$playbook.yml $extra_args
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
  prod)
    run_linters
    # Compile and bundle production javascript and css:
    npm run makeprod
    ;;
  devel)
    pip -q install -r requirements/devel.txt
    migrate_db
    compile_messages
    npm run makedevel
    ;;
  test)
    # We do not let django create test database for security reasons.
    # Database is created manually by ansible, and here we supply the
    # `--keep` option telling django to skip creating and dropping.
    python manage.py check && \
    python manage.py test --keep --reverse --failfast --verbosity 2 $extra_args
    ;;
  coverage)
    coverage run --source=. --omit='*/bot/*' manage.py test -k $extra_args
    coverage report
    ;;
  lint)
    run_linters
    ;;
  liveserver)
    TEST_LIVESERVER=1 python manage.py test --keep --liveserver=0.0.0.0:8000 --tag liveserver $extra_args
    ;;
  setup-devel|backup-db|build-bot|install-bot|install-web)
    run_ansible $action
    ;;
  prepare)
    migrate_db
    compile_messages
    # Use `-v0` to silence verbose whitenoise messages:
    python manage.py collectstatic --noinput -v0
    ;;
  *)
    set +x
    echo "usage: $0 ACTION|PLAYBOOK"
    echo "  ACTIONS:   prepare prod devel lang test lint coverage liveserver"
    echo "  PLAYBOOKS: setup-devel backup-db build-bot install-bot install-web"
    exit 1
esac

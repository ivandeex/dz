web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
botservice: python -m bot --service=1 --server=http://${DEV_HOST}${API_URL} --pollsec=20 --debug=${DEBUG}
botlog: tail -F ~/.abyss/logs/dz.log
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
prepare: ./scripts/make.sh all
makeprod: npm run makeprod
makedevel: npm run makedevel
devserver: npm run devserver
test: ./scripts/make.sh test
lint: ./scripts/make.sh lint
coverage: ./scripts/make.sh coverage
liveserver: ./scripts/make.sh liveserver

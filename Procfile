web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
botservice: python -m bot --service=1 --server=http://${DEV_HOST}${API_URL} --pollsec=20 --debug=${DEBUG}
botlog: tail -F ~/.vanko/logs/dz.log
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
prepare: ./prepare.sh all
makeprod: npm run makeprod
makedevel: npm run makedevel
devserver: npm run devserver
test: ./prepare.sh test
lint: ./prepare.sh lint
liveserver: ./prepare.sh liveserver

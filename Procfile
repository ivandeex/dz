web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
devserver: npm run devserver
makedevel: npm run makedevel
makeprod: npm run makeprod
botservice: python -m bot.main --service=1 --server=http://${DEV_HOST}${API_URL} --pollsec=20 --debug=${DEBUG}
botlog: tail -F ~/.vanko/logs/dz.log
prepare: ./prepare.sh full

web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
devserver: npm run devserver
botservice: python -m bot.main --service=1 --server=http://${DEV_HOST}${API_URL} --pollsec=30 --debug=${DEBUG}
botlog: tail -F ~/.vanko/logs/dvoznak.log
prepare: ./prepare.sh

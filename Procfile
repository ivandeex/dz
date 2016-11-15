web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
botservice: python -m bot --service=1 --server=http://${DEV_HOST}${API_URL} --pollsec=20 --debug=${DEBUG}
botlog: tail -F ~/.abyss/logs/dz.log
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
devserver: npm run devserver

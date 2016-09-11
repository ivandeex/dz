web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - web.wsgi:application
webdevel: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
devserver: npm run devserver
bot: python -m bot.bot --action=all
prepare: ./prepare.sh

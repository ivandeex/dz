web: gunicorn -w 2 -b :$PORT -e DEBUG=0 --log-file - project.wsgi:application
debug: DEBUG=1 python manage.py runserver 0.0.0.0:$WEB_PORT
hotserver: npm run hotserver
watch: npm run watch
bot: python -m bot.bot --action=all
prepare: ./ansible/prepare.sh

web: gunicorn -w2 dvoznak.web:app --log-file -
purge_news: python -m dvoznak.spider_news --action=purge
crawl_news: python -m dvoznak.spider_news --action=all
purge_tips: python -m dvoznak.spider_tips --action=purge
crawl_tips: python -m dvoznak.spider_tips --action=all

from django.utils.functional import keep_lazy_text
from django.utils.translation import ugettext_lazy
from django.template.defaultfilters import title


@keep_lazy_text
def lazy_title(text):
    return title(text)


@keep_lazy_text
def lazy_i18n_title(text):
    return lazy_title(ugettext_lazy(text))

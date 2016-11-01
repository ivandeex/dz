from django import forms
from django.utils.decorators import classproperty
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import mark_safe


class BaseModelActionForm(forms.Form):
    @classproperty
    def MODEL_CHOICES(cls):
        choices = sorted(ContentType.objects.filter(app_label='dz')
                         .values_list('model', flat=True))
        cls.MODEL_CHOICES = choices  # cache result on the class
        return choices

    model_name = forms.ChoiceField()  # choices will be set by constructor
    preserved_query = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', False)  # disable id attributes
        super(BaseModelActionForm, self).__init__(*args, **kwargs)
        self.fields['model_name'].choices = [(m, m) for m in self.MODEL_CHOICES]

    def as_hidden(self):
        return mark_safe('\n'.join(field.as_hidden() for field in self))

    def get_next_url(self):
        next_url = reverse('dz:%s-list' % self.cleaned_data['model_name'])
        preserved_query = self.cleaned_data['preserved_query']
        if preserved_query:
            next_url += '?' + preserved_query
        return next_url


class CrawlActionForm(BaseModelActionForm):
    MODEL_CHOICES = ('news', 'tip')  # override generic choices
    crawl_target = forms.CharField(max_length=12)


class RowActionForm(BaseModelActionForm):
    ACTION_CHOICES = ('delete',)
    MAX_ROWS_PER_ACTION = 100

    action = forms.ChoiceField(choices=[(a, a) for a in ACTION_CHOICES])
    row_ids = forms.RegexField(regex=r'^\d[\d,]{0,%d}$' % (MAX_ROWS_PER_ACTION * 4))

    def clean_row_ids(self):
        return [int(s) for s in self.cleaned_data['row_ids'].split(',') if s]

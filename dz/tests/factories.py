'''
Import errors in this module will make tests silently skip.
'''
import random
import factory
from operator import itemgetter
from factory import fuzzy
from factory.django import DjangoModelFactory
from django.utils import timezone
from dz import models


class FuzzyCustomDateTime(fuzzy.FuzzyDateTime):
    def __init__(self, mode):
        '''
        mode: 'today'    - since last midnight
        mode: 'recently' - last ten minutes
        '''
        if mode == 'today':
            start = timezone.now().replace(hour=0, minute=0)
        elif mode == 'recently':
            start = timezone.now() - timezone.timedelta(minutes=10)
        else:
            raise AssertionError('invalid datetime mode')
        super(FuzzyCustomDateTime, self).__init__(start, force_second=0, force_microsecond=0)


class CrawlFactory(DjangoModelFactory):
    class Meta:
        model = models.Crawl

    # Non-factory fields with prepended underscore are ignored by factory-boy
    # and can be used as factory constants.
    _CRAWL_TARGET_CHOICES = models.Crawl.CRAWL_TARGETS

    # We are using map(itemgetter) because a common list comprehension
    # [choice[0] for choice in ...] triggers a bug in factory_boy`s factory
    # metaclass: the `choice` leaks as a class field.
    _CRAWL_STATUS_CHOICES = map(itemgetter(0), models.Crawl.STATUS_CHOICES)

    target = fuzzy.FuzzyChoice(_CRAWL_TARGET_CHOICES)
    manual = fuzzy.FuzzyChoice([None, False, True])
    status = fuzzy.FuzzyChoice(_CRAWL_STATUS_CHOICES)

    started = FuzzyCustomDateTime('today')

    @factory.lazy_attribute
    def ended(self):
        duration = timezone.timedelta(minutes=random.randint(0, 5),
                                      seconds=random.randint(0, 59))
        return self.started + duration

    count = fuzzy.FuzzyInteger(0, 100)
    host = factory.Faker('first_name_female')
    pid = fuzzy.FuzzyInteger(1000, 32000)  # ORM will convert integer to string


class TipFactory(DjangoModelFactory):
    class Meta:
        model = models.Tip
        exclude = ('_spread',)

    # Fields with prepended underscore are used as factory constants.
    _SUCCESS_CODE_CHOICES = models.Tip.SUCCESS_CODE_MAP.keys()
    _LINK_CHOICES = ['http://google.com', 'http://yandex.ru', 'http://monster.de']

    # Generate 5 fake leagues limiting string to max_length of the league field.
    _LEAGUE_CHOICES = map(
        itemgetter(slice(models.Tip._meta.get_field('league').max_length)),  # => s[:max_length]
        map(lambda _: factory.Faker('country').generate({}), range(5))  # invoke faker 5 times
    )
    # Generate 5 fake parties
    _PARTY_CHOICES = map(lambda _: factory.Faker('city').generate({}), range(5))

    id = factory.Sequence(lambda n: n + 101)
    league = fuzzy.FuzzyChoice(_LEAGUE_CHOICES)

    @factory.lazy_attribute
    def parties(self):
        choices = TipFactory._PARTY_CHOICES
        return '{} - {}'.format(random.choice(choices), random.choice(choices))

    title = factory.Faker('catch_phrase')
    bookmaker = factory.Faker('name_male')

    odds = factory.LazyFunction(lambda: '%.3g' % random.uniform(1.0, 2.001))

    @factory.lazy_attribute
    def min_odds(self):
        return '%.3g' % random.uniform(1.0, float(self.odds))

    @factory.lazy_attribute
    def result(self):
        return '{}:{}'.format(random.randint(0, 100), random.randint(0, 100))

    earnings = factory.LazyFunction(lambda: '%+d' % random.randint(-5, 5))

    # `_spread` is a transient field used to calculate `spread`.
    # It is prepended by underscore but would not be ignored by factory-boy because
    # it inherits from factory class. We force factory-boy ignore it by including it
    # in the Meta.exclude list.
    _spread = fuzzy.FuzzyDecimal(-10.0, 190.0, 1)
    spread = factory.LazyAttribute(lambda self: str(self._spread))

    @factory.lazy_attribute
    def stake(self):
        end = random.choice([1, 5, 10])
        return '{}/{}'.format(random.randint(1, end), end)

    success = fuzzy.FuzzyChoice(_SUCCESS_CODE_CHOICES)
    tipster = factory.Faker('first_name_male')
    published = FuzzyCustomDateTime('today')
    updated = FuzzyCustomDateTime('today')
    crawled = FuzzyCustomDateTime('recently')
    link = fuzzy.FuzzyChoice(_LINK_CHOICES)
    archived = fuzzy.FuzzyChoice([False, True])
    text = factory.Faker('text', max_nb_chars=500)


class NewsFactory(DjangoModelFactory):
    class Meta:
        model = models.News

    _SPORT_CHOICES = ['Basketball', 'Football', 'Tennis']
    _LINK_CHOICES = TipFactory._LINK_CHOICES  # DRY
    _LEAGUE_CHOICES = TipFactory._LEAGUE_CHOICES  # DRY

    id = factory.Sequence(lambda n: n + 201)
    link = fuzzy.FuzzyChoice(_LINK_CHOICES)
    title = factory.Faker('catch_phrase')
    sport = fuzzy.FuzzyChoice(_SPORT_CHOICES)
    league = fuzzy.FuzzyChoice(_LEAGUE_CHOICES)

    @factory.lazy_attribute
    def parties(self):
        choices = TipFactory._PARTY_CHOICES
        return '{} - {}'.format(random.choice(choices), random.choice(choices))

    published = FuzzyCustomDateTime('today')
    updated = FuzzyCustomDateTime('today')
    crawled = FuzzyCustomDateTime('recently')
    archived = fuzzy.FuzzyChoice([False, True])

    # The related NewsText will be invoked *after* our News object is instantiated,
    # and the fresh News object will be passed in as the 'news' constructor argument.
    # Fully qualified class name is passed as a string to avoid circular reference,
    # relative to the current module __name__.
    newstext = factory.RelatedFactory(__name__ + '.NewsTextFactory', 'news')


class NewsTextFactory(DjangoModelFactory):
    class Meta:
        model = models.NewsText

    # We pass in newstext=None to disable RelatedFactory in NewsFactory.
    # This prevents infinite recursion between the parent and child factories.
    news = factory.SubFactory(NewsFactory, newstext=None)

    preamble = factory.Faker('text', max_nb_chars=500)
    content = factory.Faker('text', max_nb_chars=1500)

    @factory.lazy_attribute
    def datatable(self):
        # Faker's lipsum provider does not have a configurable prefix, so add it manually.
        return 'Data table: ' + factory.Faker('text').generate(dict(max_nb_chars=2000))

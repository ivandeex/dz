from vanko.utils import extract_datetime  # noqa


def first_text(sel, css):
    return (sel.css(css + ' ::text').extract_first() or '').strip()

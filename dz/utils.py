def as_choices(seq):
    return [(x, x) for x in seq]


def cut_str(text, length):
    text = text or ''
    if len(text) > length:
        text = text[:length] + '...'
    return text

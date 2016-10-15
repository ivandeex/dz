def merge_ranges(data):
    res = []
    beg = end = None
    for v in data:
        if end is None:
            beg = end = v
        elif v == end + 1:
            end = v
        else:
            res.append(str(beg) if beg == end else '%d-%d' % (beg, end))
            beg = end = v
    if end is not None:
        res.append(str(beg) if beg == end else '%d-%d' % (beg, end))
    return ','.join(res)


def split_ranges(range_str):
    res = set()
    if range_str:
        for token in range_str.split(','):
            if '-' in token:
                beg, end = token.split('-')
                for val in range(int(beg), int(end) + 1):
                    res.add(val)
            else:
                res.add(int(token))
    return res

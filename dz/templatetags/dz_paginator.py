from django import template

register = template.Library()


class PaginatorHelper(object):
    '''
    This helper class encapsulates calculations common to all page range filters.
    '''

    # Common constants (can be redefined globally):
    ON_EACH_SIDE = 3  # how many items should be shown at most on each side
    SHOW_EDGE_PAGES = True  # true value enables inclusion of first/last page items

    def __init__(self, page_obj, on_each_side=None, show_edge_pages=None):
        # default values
        if on_each_side is None:
            on_each_side = self.ON_EACH_SIDE
        if show_edge_pages is None:
            show_edge_pages = self.SHOW_EDGE_PAGES

        self.on_each_side = on_each_side
        self.cur_page = page_obj.number
        self.total_pages = page_obj.paginator.num_pages
        self.min_page = 1 if show_edge_pages else 2
        self.max_page = self.total_pages + (0 if show_edge_pages else -1)

    def left_range(self):
        start_page = max(self.min_page, self.cur_page - self.on_each_side)
        return range(start_page, self.cur_page)

    def left_has_more(self):
        return self.cur_page - self.on_each_side > self.min_page

    def right_range(self):
        end_page = min(self.cur_page + self.on_each_side, self.max_page)
        return range(self.cur_page + 1, end_page + 1)

    def right_has_more(self):
        return self.cur_page + self.on_each_side < self.max_page


@register.filter
def paginator_left_range(page_obj, on_each_side=None, show_edge_pages=None):
    '''
    The `paginator_left_range` filter accepts a `django.core.paginator.Page`
    and produces a list of 1-based page numbers to be displayed in a
    bootstrap3 paginator widget on the _left_ of the active page item.

    The list will be at most `on_each_side` long, but can be shorter
    if current page number is close to 1.
    If current page is the _first_ page, the list will be empty.

    If current page is so small that list would include _first_ page,
    it will be actually included only if `show_edge_pages` is `True`.
    If paginator widget uses a special *skip-to-first* item,
    setting `show_edge_pages` to `False` will skip _first_ page.
    '''
    return PaginatorHelper(page_obj, on_each_side, show_edge_pages).left_range()


@register.filter
def paginator_left_has_more(page_obj, on_each_side=None, show_edge_pages=None):
    '''
    The `paginator_left_has_more` filter accompanies `paginator_left_range`.
    It returns True if there are pages on the _left_ that are not included due
    to `on_each_side` limit, i.e. whether *show more* item should be displayed.
    '''
    return PaginatorHelper(page_obj, on_each_side, show_edge_pages).left_has_more()


@register.filter
def paginator_right_range(page_obj, on_each_side=None, show_edge_pages=None):
    '''
    The `paginator_right_range` filter accepts a `django.core.paginator.Page`
    and produces a list of 1-based page numbers to be displayed in a
    bootstrap3 paginator widget on the _right_ of the active page item.

    The list will be at most `on_each_side` long, but can be shorter
    if current page is close to the last one.
    If current page is the last page, the list will be empty.

    If current page is so close to the end that list would include _last_
    page, it will be actually included only if `show_edge_pages` is `True`.
    If paginator widget uses a special *skip-to-last* item,
    setting `show_edge_pages` to `False` will skip last page.
    '''
    return PaginatorHelper(page_obj, on_each_side, show_edge_pages).right_range()


@register.filter
def paginator_right_has_more(page_obj, on_each_side=None, show_edge_pages=None):
    '''
    The `paginator_right_has_more` filter accompanies `paginator_right_range`.
    It returns True if there are pages on the _right_ that are not included due
    to `on_each_side` limit, i.e. whether *show more* item should be displayed.
    '''
    return PaginatorHelper(page_obj, on_each_side, show_edge_pages).right_has_more()

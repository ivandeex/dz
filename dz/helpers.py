from django.utils.html import format_html


def user_is_admin(request):
    return request.user.has_perm('dz.is_admin')


def user_can_follow(request):
    return request.user.has_perm('dz.can_follow')


def format_external_link(request, link):
    if user_can_follow(request):
        return format_html(
            '<a href="{link}" rel="{rel}" target="_blank">{link}</a>',
            link=link, rel='nofollow noreferrer noopener'
        )
    else:
        return link

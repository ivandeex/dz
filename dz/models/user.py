from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.conf import settings
from django.db.models import signals, Q
from django.dispatch import receiver


@python_2_unicode_compatible
class User(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                primary_key=True, db_column='id', related_name='dz_user')

    username = models.CharField(_('dz user name'), max_length=20, unique=True, db_index=True)
    password = models.CharField(_('dz user password'), max_length=64)
    is_admin = models.BooleanField(_('is dz administrator'))

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('dz user')
        verbose_name_plural = _('dz users')

    @property
    def is_super(self):
        return self.username == 'admin'


@receiver(signals.pre_save, sender=User)
def _pre_save_dz_user(sender, **kwargs):
    dz_user = kwargs['instance']
    if dz_user.user_id is None:
        AuthUser = get_user_model()
        auth_user, is_new = AuthUser.objects.get_or_create(username=dz_user.username)
        if is_new:
            auth_user.save()
        dz_user.user = auth_user


@receiver(signals.post_save, sender=User)
def _post_save_dz_user(sender, **kwargs):
    dz_user = kwargs['instance']
    auth_user = dz_user.user
    auth_user.username = auth_user.first_name = dz_user.username
    auth_user.email = '%s@example.com' % dz_user.username
    auth_user.is_active = auth_user.is_staff = True

    auth_user.is_superuser = dz_user.is_super
    if not dz_user.is_super:
        auth_user.set_password(dz_user.password)

    auth_perms = auth_user.user_permissions
    perms_mgr = Permission.objects
    app_label = 'dz'
    all_dz_perms = perms_mgr.filter(content_type__app_label=app_label)

    if dz_user.is_admin:
        skip_perm_codes = ('add_crawl', 'add_news', 'add_tip', 'view_news', 'view_tips')
        auth_perms.set(all_dz_perms.filter(~Q(codename__in=skip_perm_codes)))
    else:
        view_perm_codes = ('change_news', 'change_tip', 'view_news', 'view_tips')
        auth_perms.set(all_dz_perms.filter(codename__in=view_perm_codes))

    auth_user.save()


@receiver(signals.post_save, sender=settings.AUTH_USER_MODEL)
def _post_save_auth_user(sender, **kwargs):
    auth_user = kwargs['instance']
    try:
        dz_user = auth_user.dz_user
    except User.DoesNotExist:
        return
    changed = False
    if auth_user.username != dz_user.username:
        dz_user.username = auth_user.username
        changed = True
    if auth_user._password is not None and auth_user._password != dz_user.password:
        dz_user.password = auth_user._password
        changed = True
    if changed:
        dz_user.save()


@receiver(signals.post_delete, sender=User)
def _on_delete_dz_user(sender, **kwargs):
    dz_user = kwargs['instance']
    auth_user = dz_user.user
    if not dz_user.is_super:
        auth_user.delete()

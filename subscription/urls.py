from django.conf.urls.defaults import *

import views

urlpatterns = patterns('subscription.views',
    (r'^$', 'subscription_list', {}, 'subscription_list'),
    (r'^(?P<object_id>\d+)/$', 'subscription_detail', {}, 'subscription_detail'),
    (r'^(?P<object_id>\d+)/(?P<payment_method>(standard|pro))$', 'subscription_detail', {}, 'subscription_detail'),
    )

urlpatterns += patterns('',
    (r'^paypal/', include('paypal.standard.ipn.urls')),
    (r'^done/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_done.html'), 'subscription_done'),
    (r'^change-done/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_change_done.html', extra_context=dict(cancel_url=views.cancel_url)), 'subscription_change_done'),
    (r'^cancel/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_cancel.html'), 'subscription_cancel'),
    )


# HACK: Since we need all models to be loaded and django doesn't provide such
#       signal, we have to do this in urls.py (not in models.py)
# add User.get_subscription() method
def __connect_user_get_subscription(sender, **kwargs):
    def __user_get_subscription(user):
        if not hasattr(user, '_subscription_cache'):
            sl = Subscription.objects.filter(group__in=user.groups.all())[:1]
            if sl:
                user._subscription_cache = sl[0]
            else:
                user._subscription_cache = None
        return user._subscription_cache

    if sender.__name__ == 'User':
        print sender, settings.AUTH_USER_MODEL
        get_user_model().add_to_class('get_subscription', __user_get_subscription)
class_prepared.connect(__connect_user_get_subscription)

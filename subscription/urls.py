from django.conf.urls import url, include
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


import views

urlpatterns = [
    url(r'^$', views.SubscriptionList.as_view()),
    url(r'^(?P<object_id>\d+)/$', login_required(views.SubscriptionDetail.as_view())),
    url(r'^(?P<object_id>\d+)/(?P<payment_method>(standard|pro))$', login_required(views.SubscriptionDetail.as_view())),
    ]

urlpatterns += ['',
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^done/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_done.html'), 'subscription_done'),
    url(r'^change-done/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_change_done.html', extra_context=dict(cancel_url=views.cancel_url)), 'subscription_change_done'),
    url(r'^cancel/', 'django.views.generic.simple.direct_to_template', dict(template='subscription_cancel.html'), 'subscription_cancel'),
    ]


# HACK: Since we need all models to be loaded and django doesn't provide such
#       signal, we have to do this in urls.py (not in models.py)
# add User.get_subscription() method
def __user_get_subscription(user):
    if not hasattr(user, '_subscription_cache'):
        sl = Subscription.objects.filter(group__in=user.groups.all())[:1]
        if sl:
            user._subscription_cache = sl[0]
        else:
            user._subscription_cache = None
    return user._subscription_cache

get_user_model().add_to_class('get_subscription', __user_get_subscription)

from django.conf.urls import url, include
from django.contrib.auth import get_user_model
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required


import views

urlpatterns = [
    url(r'^$', views.SubscriptionList.as_view(), name='subscription_list'),
    url(r'^(?P<object_id>\d+)/$', views.SubscriptionDetail.as_view(), name='subscription_detail'),
    url(r'^(?P<object_id>\d+)/(?P<payment_method>(standard|pro))$', login_required(views.SubscriptionDetail.as_view()), name='subscription_detail'),
    ]

urlpatterns += [
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^done/', TemplateView.as_view(template_name='subscription/subscription_done.html'), name='subscription_done'),
    url(r'^change-done/', views.SubscriptionChangeDone.as_view(), name='subscription_change_done'),
    url(r'^cancel/', TemplateView.as_view(template_name='subscription/subscription_cancel.html'), name='subscription_cancel'),
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

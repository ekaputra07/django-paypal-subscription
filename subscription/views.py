import datetime, decimal, urllib

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import paypal_form

from models import Subscription, UserSubscription

class SubscriptionList(TemplateView):
    template_name = 'subscription_list.html'

    def get_context_data(self, **kwargs):
        return dict(object_list = Subscription.objects.all())


class SubscriptionDetail(TemplateView):
    template_name = 'subscription_detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SubscriptionDetail, self).dispatch(*args, **kwargs)

    def get(self, request, object_id, **kwargs):
        payment_method = kwargs.get('payment_method', 'standard')
        from subscription.providers import PaymentMethodFactory
        # See PROPOSALS section in providers.py
        if payment_method == "pro":
            domain = Site.objects.get_current().domain
            item = {"amt": s.price,
                    "inv": "inventory",         # unique tracking variable paypal
                    "custom": "tracking",       # custom tracking variable for you
                    "cancelurl": 'http://%s%s' % (domain, reverse('subscription_cancel')),  # Express checkout cancel url
                    "returnurl": 'http://%s%s' % (domain, reverse('subscription_done'))}  # Express checkout return url

            data = {"item": item,
                    "payment_template": "payment.html",      # template name for payment
                    "confirm_template": "confirmation.html", # template name for confirmation
                    "success_url": reverse('subscription_done')}              # redirect location after success

            o = PaymentMethodFactory.factory('WebsitePaymentsPro', data=data, request=request)
            # We return o.proceed() just because django-paypal's PayPalPro returns HttpResponse object
            return o.proceed()
        return super(SubscriptionDetail, self).get(self, request, object_id, **kwargs)

    def get_context_data(self, **kwargs):
        object_id = self.kwargs['object_id']
        payment_method = self.kwargs.get('payment_method', 'standard')
        request = self.request
        s = get_object_or_404(Subscription, id=object_id)
        try:
            us = request.user.usersubscription_set.get(
                active=True)
        except UserSubscription.DoesNotExist:
            change_denied_reasons = None
            us = None
        else:
            change_denied_reasons = us.try_change(s)

        if change_denied_reasons:
            form = None
        else:
            form = s.get_paypal_form(request.user, us)
        try:
            s_us = request.user.usersubscription_set.get(subscription=s)
        except UserSubscription.DoesNotExist:
            s_us = None

        if payment_method == 'standard':
            return dict(object=s, usersubscription=s_us,
                        change_denied_reasons=change_denied_reasons,
                        form=form, cancel_url=paypal_form.cancel_url)
        else:
            #should never get here
            raise Http404


class SubscriptionChangeDone(TemplateView):
    template_name = 'subscription_change_done.html'

    def get_context_data(self, **kwargs):
        return dict(cancel_url=cancel_url)

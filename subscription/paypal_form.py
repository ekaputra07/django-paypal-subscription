from django.conf import settings
from django.dispatch import Signal
from django.core.urlresolvers import reverse
import urllib

from django.contrib.sites.models import Site

_formclass = getattr(settings, 'SUBSCRIPTION_PAYPAL_FORM', 'paypal.standard.forms.PayPalPaymentsForm')
_formclass_dot = _formclass.rindex('.')
_formclass_module = __import__(_formclass[:_formclass_dot], {}, {}, [''])
PayPalForm = getattr(_formclass_module, _formclass[_formclass_dot+1:])


get_paypal_extra_args = Signal(providing_args=['user', 'subscription', 'extra_args'])

# http://paypaldeveloper.com/pdn/board/message?board.id=basicpayments&message.id=621
if settings.PAYPAL_TEST:
    cancel_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)
else:
    cancel_url = 'https://www.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)

# https://cms.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=developer/e_howto_html_Appx_websitestandard_htmlvariables

def _paypal_form_args(upgrade_subscription=False, **kwargs):
    "Return PayPal form arguments derived from kwargs."
    def _url(rel):
        if not rel.startswith('/'): rel = '/'+rel
        return 'http://%s%s' % ( Site.objects.get_current().domain, rel )

    if upgrade_subscription: returl = reverse('subscription_change_done')
    else: returl = reverse('subscription_done')

    rv = settings.SUBSCRIPTION_PAYPAL_SETTINGS.copy()
    rv.update( notify_url = _url(reverse('paypal-ipn')),
               return_url = _url(returl),
               cancel_return = _url(reverse("subscription_cancel")),
               **kwargs)
    return rv

def _paypal_form(subscription, user, upgrade_subscription=False, **extra_args):
    # if not user.is_authenticated: return None

    if subscription.recurrence_unit:
        if not subscription.trial_unit:
            trial = {}
        else:
            trial = {
                'a1': 0,
                'p1': subscription.trial_period,
                't1': subscription.trial_unit,
                }
        kwargs = {}
        kwargs.update(trial)
        kwargs.update(extra_args)
        return PayPalForm(
            initial = _paypal_form_args(
                cmd='_xclick-subscriptions',
                item_name='%s: %s' % ( Site.objects.get_current().name,
                                       subscription.name ),
                item_number = subscription.id,
                custom = user.id,
                a3=subscription.price,
                p3=subscription.recurrence_period,
                t3=subscription.recurrence_unit,
                src=1,                  # make payments recur
                sra=1,            # reattempt payment on payment error
                upgrade_subscription=upgrade_subscription,
                modify=upgrade_subscription and 2 or 0, # subscription modification (upgrade/downgrade)
                **kwargs),
            button_type='subscribe'
            )
    else:
        return PayPalForm(
            initial = _paypal_form_args(
                item_name='%s: %s' % ( Site.objects.get_current().name,
                                       subscription.name ),
                item_number = subscription.id,
                custom = user.id,
                amount=subscription.price))

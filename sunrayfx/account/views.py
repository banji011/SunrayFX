from django.contrib import messages
from django.conf import settings
from django.http import  HttpResponse,HttpResponseRedirect
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.views.generic import ListView
from django.urls import reverse
from paystackapi.paystack import Paystack
from .models import Membership, UserMembership, Subscription
import requests
paystack_secret_key = settings.PAYSTACK_SECRET_KEY

paystack = Paystack(secret_key=paystack_secret_key)

def profile_view(request):
    user_membership = get_user_membership(request)
    user_subscription = get_user_subscription(request)
    context = {
        'user_membership':user_membership,
        'user_subscription': user_subscription
    }
    return render(request, 'account/profile.html',context)
 
def get_user_membership(request):
    user_membership_qs = UserMembership.objects.filter(user=request.user)
    if user_membership_qs.exists():
        return user_membership_qs.first()
    return None 


def get_user_subscription(request):
    user_subscription_qs = Subscription.objects.filter(
        user_membership = get_user_membership(request))
    if user_subscription_qs.exists():
        user_subscription = user_subscription_qs.first()
        return user_subscription
    return None 

def get_selected_membership(request):
    membership_type = request.session['selected_membership_type']
    selected_membership_qs = Membership.objects.filter(membership_type = membership_type) 
    if selected_membership_qs.exists():
        return selected_membership_qs.first()
    return None 
    
 
class MembershipSelectView(ListView):
    model = Membership

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)    
        current_membership = get_user_membership(self.request)
        context['current_membership'] = str(current_membership.membership)
        return context

    def post(self, request, **kwargs):
        selected_membership_type = request.POST.get('membership_type')
        print(selected_membership_type)
        user_membership = get_user_membership(request)
        print(user_membership.membership)
        user_subscription = get_user_subscription(request)
        
        
        selected_membership_qs = Membership.objects.filter(
            membership_type = selected_membership_type)
        
        if selected_membership_qs.exists():            
            selected_membership = selected_membership_qs.first()
            
            
        if user_membership.membership == selected_membership:
            if user_subscription != None:
                messages.info(request, f'you already have this membership, your next payment is due  ')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        request.session['selected_membership_type'] = selected_membership.membership_type

        return HttpResponseRedirect(reverse('account:payment'))


def PaymentView(request):
    user_membership = get_user_membership(request)

    selected_membership = get_selected_membership(request)
    paystack_secret_key = settings.PAYSTACK_SECRET_KEY

    if request.method == "POST":
        
        reference = request.POST['paystackToken']
        print(reference)
        headers = {'Authorization': f'Bearer {paystack_secret_key}'}
        resp = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        response =resp.json()
        auth_code = response['data']['authorization']['authorization_code']
        subscription = paystack.subscription.create(
            customer=user_membership.paystack_customer_id,
            plan = selected_membership.paystack_plan_id,
            authorization= auth_code
        )
        print(response['status'])
        print(response['data']['authorization']['authorization_code'])
        messages.success(request, "Your card was charged !")
        return redirect(reverse('account:update-transactions',
        kwargs={
            'subscription_id':subscription['data']['id']
        }
        ))
    context = {
        'paystack_secret_key': paystack_secret_key,
        'selected_membership' : selected_membership
    }

    return render(request, 'account/membership_payment.html', context)


def updateTransactions(request, subscription_id):
    user_membership = get_user_membership(request)
    selected_membership = get_selected_membership(request)
    
    user_membership.membership = selected_membership
    user_membership.save()

    sub, created = Subscription.objects.get_or_create(user_membership=user_membership)
    sub.paystack_subscription_id = subscription_id
    sub.active = True
    sub.save()

    try:
        del request.session['selected_membership_type']
    except:
        pass
    messages.info(request, f'successfully created {selected_membership} membership')
    return redirect('/tutorial')

def cancelSubscription(request):
    user_sub = get_user_subscription(request)

    if user_sub.active == False:
        messages.info(request, "You do not have an active subscription ! ")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
    sub = paystack.subscription.fetch(user_sub.paystack_subscription_id)
    email_token = sub['data']['email_token']
    subscription_code = sub['data']['subscription_code']
    del_sub = paystack.subscription.disable(code=subscription_code,token=email_token)

    user_sub.active = False
    user_sub.save()

    free_membership = Membership.objects.filter(membership_type='Free').first()
    user_membership = get_user_membership(request)
    user_membership.membership = free_membership
    user_membership.save()

    messages.info(request, "Successfully cancelled membership. We have sent an email")

    return redirect('/account')
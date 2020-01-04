from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from paystackapi.paystack import Paystack
from datetime import datetime
paystack_secret_key = settings.PAYSTACK_SECRET_KEY

paystack = Paystack(secret_key=paystack_secret_key)


MEMBERSHIP_CHOICES = (
    ('Enterprise', 'enterprise'),
    ('Standard', 'standard'),
    ('Free', 'free')
) 

class Membership(models.Model):
    slug = models.SlugField()
    membership_type = models.CharField(
                    choices = MEMBERSHIP_CHOICES,
                    default = 'Free',
                    max_length = 30)
    price = models.IntegerField(default=10)
    paystack_plan_id = models.CharField(max_length=40)

    def __str__(self):
        return self.membership_type

class UserMembership(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    paystack_customer_id = models.CharField(max_length=40)
    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username



class Subscription(models.Model):
    user_membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE)
    paystack_subscription_id = models.CharField(max_length=40)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user_membership.user.username

    @property
    def get_created_date(self):
        subscription = paystack.subscription.fetch(self.paystack_subscription_id)
        date = datetime.strptime(subscription['data']['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return date.strftime("%Y-%m-%d, %H:%M:%S")
        
    
    @property
    def get_next_billing_date(self):
        subscription = paystack.subscription.fetch(self.paystack_subscription_id)
        date = datetime.strptime(subscription['data']['next_payment_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return date.strftime("%Y-%m-%d, %H:%M:%S")
 

def post_save_usermembership_create(sender, instance, created, *args, **kwargs):
    if created:
        UserMembership.objects.get_or_create(user=instance)

    user_membership, created = UserMembership.objects.get_or_create(user=instance)
    if user_membership.paystack_customer_id is None or user_membership.paystack_customer_id == '':
        new_customer = paystack.customer.create(email=instance.email)
        user_membership.paystack_customer_id = new_customer['data']['id']
        user_membership.save()

post_save.connect(post_save_usermembership_create,sender=settings.AUTH_USER_MODEL )

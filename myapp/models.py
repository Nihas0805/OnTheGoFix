from django.db import models

from django.contrib.auth.models import AbstractUser,User

from django.utils.translation import gettext_lazy as _

from django.db.models.signals import post_save

from random import randint


class BaseModel(models.Model):

    created_date=models.DateTimeField(auto_now_add=True)

    updated_date=models.DateTimeField(auto_now=True)

    is_active=models.BooleanField(default=True)


class User(AbstractUser):

    role_choices = [
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
    ]

    role = models.CharField(max_length=20, choices=role_choices,default="customer")

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    is_verified=models.BooleanField(default=False)

    otp=models.CharField(max_length=6,null=True,blank=True)

    def generate_otp(self):

        self.otp=str(randint(1000,9000))

        self.save()


class CustomerProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')

    address = models.CharField(max_length=200, blank=True ,null=True)

    def _str_(self):
        return self.user.username


class ServiceType(models.Model):
    
    vehicle_type_choices = [
        ('two_wheeler', 'Two wheeler'),
        ('four_wheeler', 'Four Wheeler'),
        ('others', 'Others'),
        ]

    vehicle_type = models.CharField(max_length=20, choices=vehicle_type_choices, default='two_wheeler')

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True, null=True)

    def _str_(self):
        return self.name
  


class ServiceProviderProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')

    service_types = models.ManyToManyField(ServiceType, related_name='providers')

    address = models.CharField(max_length=200, blank=True ,null=True)

    availability_status = models.BooleanField(default=True)  
    
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def _str_(self):
        return self.user.username


class BreakdownRequest(BaseModel):
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breakdown_requests')

    service_provider = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_requests')

    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='requests')

    description = models.TextField()

    image = models.ImageField(upload_to='images/', blank=True, null=True)

    status_choices = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ]

    status = models.CharField(max_length=20, choices=status_choices, default='pending')

    latitude = models.FloatField(blank=True,null=True)

    longitude = models.FloatField(blank=True,null=True)

    completed_at = models.DateTimeField(blank=True, null=True)

    def _str_(self):
        return f"{self.customer.user.username} - {self.service_type.name} ({self.status})"



class Payment(BaseModel):

    breakdown_request = models.OneToOneField(BreakdownRequest, on_delete=models.CASCADE, related_name='payment')

    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_done')

    amount = models.PositiveIntegerField()

    payment_choices=[
                    ('cod', 'cod'), 
                    ('razorpay', 'razorpay')
                    ]

    payment_method = models.CharField(max_length=50, choices=payment_choices)

    payment_status_choices=[
                           ('pending', 'Pending'),  
                           ('completed', 'Completed')
                           ]


    payment_status = models.CharField(max_length=20, choices=payment_status_choices, default='pending')
    
    def _str_(self):
        return f"Payment of {self.amount} from {self.customer.user.username} to {self.service_provider.user.username}"

    
class Rating(models.Model):

    breakdown_request = models.OneToOneField(BreakdownRequest, on_delete=models.CASCADE, related_name='rating')

    service_provider = models.ForeignKey(ServiceProviderProfile, on_delete=models.CASCADE, related_name='ratings')

    rating = models.PositiveIntegerField()

    review = models.TextField(blank=True, null=True)

    created_date=models.DateTimeField(auto_now_add=True)
   
    def _str_(self):
        return f"Rating for {self.service_provider.user.username}: {self.rating}"


class ServiceHistory(models.Model):

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_delivered')

    breakdown_request = models.ForeignKey(BreakdownRequest, on_delete=models.CASCADE)

    def _str_(self):
        return f"History for {self.customer.user.username} - {self.breakdown_request}"

class ServiceProviderDashBoard(models.Model):

    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offered_services')

    breakdown_request = models.ForeignKey(BreakdownRequest, on_delete=models.CASCADE)

    Payment_details=models.ForeignKey(Payment,on_delete=models.CASCADE)

    def _str_(self):
        return f"{self.service_provider.user.username} - Request TYPE: {self.breakdown_request.service_type} - Payment ID: {self.Payment_details.id}"

from django.db.models.signals import post_save

from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'customer':
            CustomerProfile.objects.create(user=instance)
        elif instance.role == 'provider':
            ServiceProviderProfile.objects.create(user=instance)


    

   

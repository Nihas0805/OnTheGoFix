from django.db import models

from django.contrib.auth.models import AbstractUser

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

        self.otp=str(randint(1000,9000))+str(self.id)

        self.save()


class CustomerProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')

    address = models.CharField(max_length=200, blank=True ,null=True)

    def __str__(self):
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

    def __str__(self):
        return self.name
  


class ServiceProviderProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')

    service_types = models.ManyToManyField(ServiceType, related_name='providers')

    address = models.CharField(max_length=200, blank=True ,null=True)

    availability_status = models.BooleanField(default=True)  
    
    profile_picture = models.ImageField(upload_to='profilepictures/', blank=True, null=True, default="profilepictures/default.png")
    
    def __str__(self):
        return self.user.username

class BreakdownRequest(BaseModel):
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breakdown_requests')

    service_provider = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_requests')

    service_types = models.ManyToManyField(ServiceType, related_name='breakdown_requests')  

    description = models.TextField(null=True)

    image = models.ImageField(upload_to='images/', blank=True, null=True)

    status_choices = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('pick_up', 'Pick up Completed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ]

    status = models.CharField(max_length=20, choices=status_choices, default='pending')

    latitude = models.FloatField(blank=True,null=True)

    longitude = models.FloatField(blank=True,null=True)

    completed_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f"{self.customer.username} - {self.status}"



class Payment(BaseModel):

    breakdown_request = models.OneToOneField(BreakdownRequest, on_delete=models.CASCADE, related_name='payment')

    amount = models.PositiveIntegerField()

    payment_choices=[
                    ('cod', 'cod'), 
                    ('razorpay', 'razorpay')
                    ]

    payment_method = models.CharField(max_length=50, choices=payment_choices ,default='cod')

    payment_status_choices=[
                           ('pending', 'Pending'),  
                           ('completed', 'Completed')
                           ]


    payment_status = models.CharField(max_length=20, choices=payment_status_choices, default='pending')

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f" Payment of {self.amount} from {self.customer.user.username} to {self.service_provider.user.username}"




    
class Rating(models.Model):

    breakdown_request = models.OneToOneField(BreakdownRequest, on_delete=models.CASCADE, related_name='rating')

    rating = models.PositiveIntegerField(default=5)

    review = models.TextField(blank=True, null=True)

    created_date=models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return f"Rating for {self.service_provider.user.username}: {self.rating}"




from django.db.models.signals import post_save

from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'customer':
            CustomerProfile.objects.create(user=instance)
        elif instance.role == 'provider':
            ServiceProviderProfile.objects.create(user=instance)




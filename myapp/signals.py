from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from myapp.models import BreakdownRequest
from django.utils.timezone import now
from decouple import config



def send_email(subject, body, recipient_list):
    send_mail(
        subject,
        body,
        config('DEFAULT_FROM_EMAIL'),
        recipient_list,
        fail_silently=False,
    )

@receiver(post_save, sender=BreakdownRequest)
def notify_on_breakdown_request(sender, instance, created, **kwargs):
    customer = instance.customer
    service_provider = instance.service_provider

    if created:  
        
        send_email(
            subject="Breakdown Request Submitted",
            body="Your request has been successfully sent to the service provider.",
            recipient_list=[customer.email]
        )

        send_email(
            subject="New Breakdown Request",
            body="You have received a new breakdown request.",
            recipient_list=[service_provider.email]
        )

    if instance.status == 'accepted' :
        
        send_email(
            subject="Service Accepted",
            body="Your service request has been Accepted.",
            recipient_list=[customer.email]
        )
    if instance.status == 'delivered' :
        
        send_email(
            subject="Service Completed",
            body="Your service request has been completed and delivered.",
            recipient_list=[customer.email]
        )


        

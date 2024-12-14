from django.shortcuts import render,redirect,get_object_or_404

from django.views.generic import View,FormView

from myapp.forms import SignUpForm,SignInForm,ServiceProviderProfileForm,BreakdownRequestCreateForm,CustomerProfileForm,BreakdownRequestUpdateForm

from django.core.mail import send_mail

from django.contrib import messages

from twilio.rest import Client

from myapp.models import User,BreakdownRequest,ServiceProviderProfile,BreakdownRequest,CustomerProfile,ServiceType

from django.contrib.auth import authenticate,login

from django.urls import reverse_lazy

from django.db.models import Case, When, Value, IntegerField



def send_otp_phone(otp):
    account_sid = "ACf59b762f511f7abd4d7ae2872eaf9107"
    auth_token = "ce219a2f217f965cdf8b7146b5441503"
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
        messaging_service_sid='MGf6cbeb77420eb2770cd2b66be77db8f8',
        body=otp,
        to='+919048444482',
        )
        print(message.sid)
    
    except Exception as e: 
        print(e)

def send_otp_email(user):

    user.generate_otp()

    send_otp_phone(user.otp)

    subject="verify your email"

    message=f"OTP for account verification is {user.otp}"

    from_email="nihasansin010@gmail.com"

    to_email={user.email}

    send_mail(subject,message,from_email,to_email)



class SignUpView(View):

    template_name="register.html"

    form_class=SignUpForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):

        form_data=request.POST

        form_instance=self.form_class(form_data)

        if form_instance.is_valid():

            user_object=form_instance.save(commit=False)

            user_object.is_active=False

            user_object.save()

            send_otp_email(user_object)

            return redirect("verify-email")
        
        return render(request,self.template_name,{"form":form_instance})

class VerifyEmailView(View):

    template_name="verify_email.html"

    def get(self,request,*args,**kwargs):

        return render(request,self.template_name)

    def post(self,request,*args,**kwargs):

        otp=request.POST.get("otp")
        
        try:

            user_object=User.objects.get(otp=otp)

            user_object.is_active=True

            user_object.is_verified=True

            user_object.otp=None

            user_object.save()

            return redirect("signin")

        except:

            messages.error(request,"Invalid otp")

            return render(request,self.template_name)





class CustomerIndexView(View):
    template_name = "customer_index.html"

    def get(self, request, *args, **kwargs):
        qs = ServiceProviderProfile.objects.prefetch_related('service_types').all().order_by('-availability_status')
        
        # Fetch distinct vehicle types to filter in template
        vehicle_types = ServiceType.objects.values_list('vehicle_type', flat=True).distinct()

        data = {
            "providers": qs,
            "vehicle_types": vehicle_types
        }
        return render(request, self.template_name, data)


        





class ProviderIndexView(View):
    template_name = "provider_index.html"

    def get(self, request, *args, **kwargs):
        # Fetch the breakdown requests assigned to the service provider
        qs = BreakdownRequest.objects.filter(service_provider=request.user, status='pending').order_by('created_date')

        return render(request, self.template_name, {"data": qs})

    def post(self, request, *args, **kwargs):
        # Extract the action (accept or cancel) and request_id from the POST data
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

        # Fetch the breakdown request object
        breakdown_request = BreakdownRequest.objects.filter(id=request_id).first()

        if breakdown_request:
            # Perform the action based on the button clicked
            if action == "accept":
                breakdown_request.status = "accepted"
            elif action == "cancel":
                breakdown_request.status = "cancelled"

            # Save the updated request
            breakdown_request.save()

        # Re-fetch the updated queryset to display the latest breakdown requests
        qs = BreakdownRequest.objects.filter(service_provider=request.user, status='pending').order_by('created_date')

        # Redirect back to the list page with the updated queryset
        return render(request, self.template_name, {"data": qs})


class SignInView(FormView):

    template_name="login.html"

    form_class=SignInForm

    def post(self,request,*args,**kwargs):

        form_instance=self.form_class(request.POST)

        if form_instance.is_valid():

            username=form_instance.cleaned_data.get("username")

            password=form_instance.cleaned_data.get("password")

            user_object=authenticate(username=username,password=password)

            if user_object is not None:

                login(request,user_object)

                if user_object.role == 'customer':
                    return redirect('customer-index')  
                elif user_object.role == 'provider':
                    return redirect('provider-index')  
            else:
                form.add_error(None, "Invalid username or password")
        return render(request, self.template_name, {'form': form_instance})
    




class ServiceProviderProfileEditView(View):
    template_name = "provider_profile_edit.html"
    form_class = ServiceProviderProfileForm

    def get(self, request, *args, **kwargs):
        # Fetch the user's profile object or create one if it doesn't exist
        profile_object, created = ServiceProviderProfile.objects.get_or_create(user=request.user)
        form_instance = self.form_class(instance=profile_object, user=request.user)
        return render(request, self.template_name, {"form": form_instance})

    def post(self, request, *args, **kwargs):
        # Fetch the user's profile object or create one if it doesn't exist
        profile_object, created = ServiceProviderProfile.objects.get_or_create(user=request.user)
        
        # Bind POST data and FILES to the form instance
        form_instance = self.form_class(request.POST, request.FILES, instance=profile_object, user=request.user)
        
        if form_instance.is_valid():
            print("Form is valid. Saving data...")
            profile = form_instance.save(commit=False)
            profile.user = request.user  # Explicitly link the profile to the user
            profile.save()
            form_instance.save_m2m()  # Save many-to-many relationships
            print("Uploaded file:", request.FILES.get('profile_picture'))
            return redirect("provider-index")
        else:
            print("Form errors:", form_instance.errors)  # Debug form errors
            print("POST Data:", request.POST)           # Debug POST data
            print("FILES Data:", request.FILES)         # Debug FILE data

        return render(request, self.template_name, {"form": form_instance})








from django.contrib.auth.mixins import LoginRequiredMixin


class ProviderProfileView(LoginRequiredMixin, View):
    template_name = "provider_profile.html"

    def get(self, request, *args, **kwargs):
        try:
            profile = ServiceProviderProfile.objects.prefetch_related('service_types').get(user=request.user)
            
            # Group services under vehicle types
            grouped_services = {
                'two_wheeler': profile.service_types.filter(vehicle_type='two_wheeler'),
                'four_wheeler': profile.service_types.filter(vehicle_type='four_wheeler'),
                'others': profile.service_types.filter(vehicle_type='others'),
            }
        except ServiceProviderProfile.DoesNotExist:
            profile = None
            grouped_services = None

        context = {
            "profile": profile,
            "grouped_services": grouped_services,
        }
        return render(request, self.template_name, context)




   



class BreakdownRequestCreateView(LoginRequiredMixin, View):

    template_name = 'breakdownrequest_create.html'

    def get(self, request, *args, **kwargs):
        # Get the service provider ID from the URL
        service_provider_id = kwargs.get('service_provider_id')

        # Fetch the service provider details
        service_provider = ServiceProviderProfile.objects.filter(user_id=service_provider_id).first()

        if not service_provider:
            # Redirect if the service provider does not exist
            return redirect('customer-index')  # Replace 'customer-index' with the appropriate URL

        # Initialize the form with the service provider and user context
        form = BreakdownRequestCreateForm(service_provider=service_provider, user=request.user)

        # Render the template with form and service provider data
        return render(request, self.template_name, {'form': form, 'service_provider': service_provider})

    def post(self, request, *args, **kwargs):
    # Get the service provider ID and details
        service_provider_id = kwargs.get('service_provider_id')
        service_provider = ServiceProviderProfile.objects.filter(user_id=service_provider_id).first()

        if not service_provider:
            return redirect('customer-index')  # Redirect if service provider doesn't exist

        # Pass the POST data and file data to the form
        form = BreakdownRequestCreateForm(request.POST, request.FILES, service_provider=service_provider, user=request.user)

        if form.is_valid():
            # Create a breakdown request instance but don't save yet
            breakdown_request = form.save(commit=False)

            # Assign the logged-in user as the customer
            breakdown_request.customer = request.user

            # Assign the selected service provider
            breakdown_request.service_provider = service_provider.user

            # Save the breakdown request instance
            breakdown_request.save()

            # Save many-to-many field (service_types)
            form.save_m2m()

            customer_address = form.cleaned_data.get('customer_address')
            if request.user.customer_profile:
                request.user.customer_profile.address = customer_address
                request.user.customer_profile.save()

            # Redirect to a success or index page
            return redirect('customer-index')  # Replace with an appropriate success URL

        # If form is not valid, render the form with error messages
        return render(request, self.template_name, {'form': form, 'service_provider': service_provider})             



class CustomerProfileEditView(View):
    template_name = 'customer_profile_edit.html'

    form_class = CustomerProfileForm

    def get(self,request,*args,**kwargs):

        profile_object=CustomerProfile.objects.get(user=request.user)

        form_instance=self.form_class(user=request.user,instance=profile_object)

        return render(request,self.template_name,{"form":form_instance})

    def post(self, request, *args, **kwargs):

        profile_object = CustomerProfile.objects.get(user=request.user)

        form_instance = self.form_class(request.POST, request.FILES, instance=profile_object, user=request.user)

        if form_instance.is_valid():
            form_instance.save()
            return redirect("customer-index")

        return render(request, self.template_name, {"form": form_instance})

class CustomerProfileListView(View):
    
    template_name="customer_profile.html"

    def get(self,request,*args,**kwargs):

        qs=CustomerProfile.objects.get(user=request.user)

        return render(request,self.template_name,{"data":qs})


from django.utils.timezone import now

class BreakdownRequestUpdateView(View):
    template_name = "breakdownrequest_edit.html"

    def get(self, request, *args, **kwargs):
        # Get the pk from kwargs and use it to fetch the breakdown request
        pk = kwargs.get('pk')
        try:
            # Fetch the breakdown request object using pk
            breakdown_request = BreakdownRequest.objects.get(pk=pk)
        except BreakdownRequest.DoesNotExist:
            return redirect("provider-index")  # Redirect if not found

        # Initialize the form with the existing data
        form = BreakdownRequestUpdateForm(instance=breakdown_request)

        return render(request, self.template_name, {"form": form, "breakdown_request": breakdown_request})

    def post(self, request, *args, **kwargs):
        # Get the pk from kwargs and use it to fetch the breakdown request
        pk = kwargs.get('pk')
        try:
            # Fetch the breakdown request object using pk
            breakdown_request = BreakdownRequest.objects.get(pk=pk)
        except BreakdownRequest.DoesNotExist:
            return redirect("provider-index")  # Redirect if not found

        # Initialize the form with POST data
        form = BreakdownRequestUpdateForm(request.POST, request.FILES, instance=breakdown_request)

        if form.is_valid():
            updated_request = form.save(commit=False)

            # Check which button was clicked (Take Action or Cancel)
            if 'take_action' in request.POST:
                updated_request.status = 'accepted'
            elif 'cancel' in request.POST:
                updated_request.status = 'cancelled'

            # If status is completed, populate the `completed_at` field
            if updated_request.status == 'completed':
                updated_request.completed_at = now()
            else:
                updated_request.completed_at = None

            updated_request.save()
            return redirect("provider-index")  # Redirect to the list view or wherever you want

        return render(request, self.template_name, {"form": form, "breakdown_request": breakdown_request})

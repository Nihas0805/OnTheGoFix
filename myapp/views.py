from django.shortcuts import render,redirect,get_object_or_404

from django.views.generic import View,FormView

from myapp.forms import SignUpForm,SignInForm,ServiceProviderProfileForm,BreakdownRequestCreateForm,CustomerProfileForm,BreakdownRequestUpdateForm

from django.core.mail import send_mail

from django.contrib import messages

from twilio.rest import Client

from myapp.models import User,BreakdownRequest,ServiceProviderProfile,BreakdownRequest,CustomerProfile,ServiceType,Payment

from django.contrib.auth import authenticate,login,logout

from django.urls import reverse_lazy

from django.db.models import Case, When, Value, IntegerField

from decouple import config

from django.http import JsonResponse




def send_otp_phone(otp):
    account_sid = config('TWILIO_ACCOUNT_SID')
    auth_token = config('TWILIO_AUTH_TOKEN')
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
        # Fetch pending breakdown requests for the current service provider
        qs = BreakdownRequest.objects.filter(service_provider=request.user, status='pending').order_by('created_date')

        breakdown_data = []
        for request_instance in qs:
            try:
                # Group services under vehicle types
                grouped_services = {
                    'two_wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
                    'four_wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
                    'others': request_instance.service_types.filter(vehicle_type='others'),
                }
            except ServiceType.DoesNotExist:
                grouped_services = None

            # Append processed request data
            breakdown_data.append({
                "request": request_instance,
                "grouped_services": grouped_services,
            })

        # Pass structured data to the template
        context = {
            "data": breakdown_data,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Handle the accept or cancel action
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

        # Fetch and update the status of the breakdown request
        breakdown_request = BreakdownRequest.objects.filter(id=request_id).first()
        if breakdown_request:
            if action == "accept":
                breakdown_request.status = "accepted"
            elif action == "cancel":
                breakdown_request.status = "cancelled"
            breakdown_request.save()

        # Redirect back to the updated view
        return self.get(request, *args, **kwargs) 




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
                form_instance.add_error(None, "Invalid username or password")
        return render(request, self.template_name, {'form': form_instance})

class LogoutView(View):
    
    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect("signin")
    




class ServiceProviderProfileEditView(View):
    template_name = "provider_profile_edit.html"
    form_class = ServiceProviderProfileForm

    def get(self, request, *args, **kwargs):
        # Fetch the user's profile object or create one if it doesn't exist
        profile_object = ServiceProviderProfile.objects.get(user=request.user)
        form_instance = self.form_class(instance=profile_object, user=request.user)
        return render(request, self.template_name, {"form": form_instance})

    def post(self, request, *args, **kwargs):
        # Fetch the user's profile object or create one if it doesn't exist
        profile_object = ServiceProviderProfile.objects.get(user=request.user)
        
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
        service_provider_id = kwargs.get('service_provider_id')
        service_provider = ServiceProviderProfile.objects.filter(user_id=service_provider_id).first()

        if not service_provider:
            return redirect('customer-index')  # Redirect if service provider doesn't exist

        form = BreakdownRequestCreateForm(service_provider=service_provider, user=request.user)
        return render(request, self.template_name, {'form': form, 'service_provider': service_provider})

    def post(self, request, *args, **kwargs):
        service_provider_id = kwargs.get('service_provider_id')
        service_provider = ServiceProviderProfile.objects.filter(user_id=service_provider_id).first()

        if not service_provider:
            return redirect('customer-index')

        form = BreakdownRequestCreateForm(request.POST, request.FILES, service_provider=service_provider, user=request.user)

        if form.is_valid():
            breakdown_request = form.save(commit=False)
            breakdown_request.customer = request.user
            breakdown_request.service_provider = service_provider.user
            breakdown_request.save()
            form.save_m2m()

            # Update customer address
            customer_address = form.cleaned_data.get('customer_address')
            if request.user.customer_profile:
                request.user.customer_profile.address = customer_address
                request.user.customer_profile.save()

            return redirect('customer-index')

        return render(request, self.template_name, {'form': form, 'service_provider': service_provider})

class ProviderBreakdownRequestDetailView(View):
    template_name = "breakdownrequest_provider_detail.html"

    def get(self, request, *args, **kwargs):
        id = kwargs.get("pk")

        # Fetch a single BreakdownRequest object
        try:
            request_instance = BreakdownRequest.objects.get(id=id)
        except BreakdownRequest.DoesNotExist:
            return render(request, self.template_name, {"error": "Breakdown request not found."})

        try:
            # Group services under vehicle types
            grouped_services = {
                'two_wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
                'four_wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
                'others': request_instance.service_types.filter(vehicle_type='others'),
            }
        except ServiceType.DoesNotExist:
            grouped_services = None

        # Prepare context data for the template
        breakdown_data = {
            "request": request_instance,
            "grouped_services": grouped_services,
        }

        context = {
            "data": [breakdown_data],  # Wrap in a list to maintain template structure
        }
        return render(request, self.template_name, context)

class CustomerBreakdownRequestDetailView(View):
    template_name = "breakdownrequest_customer_detail.html"

    def get(self, request, *args, **kwargs):
        id = kwargs.get("pk")

        # Fetch a single BreakdownRequest object
        try:
            request_instance = BreakdownRequest.objects.get(id=id)
        except BreakdownRequest.DoesNotExist:
            return render(request, self.template_name, {"error": "Breakdown request not found."})

        try:
            # Group services under vehicle types
            grouped_services = {
                'two_wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
                'four_wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
                'others': request_instance.service_types.filter(vehicle_type='others'),
            }
        except ServiceType.DoesNotExist:
            grouped_services = None

        # Prepare context data for the template
        breakdown_data = {
            "request": request_instance,
            "grouped_services": grouped_services,
        }

        context = {
            "data": [breakdown_data],  # Wrap in a list to maintain template structure
        }
        return render(request, self.template_name, context)

          



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
            if updated_request.status == 'delivered':
                updated_request.completed_at = now()
            else:
                updated_request.completed_at = None

            updated_request.save()
            return redirect('provider-dashboard')
              # Redirect to the list view or wherever you want

        return render(request, self.template_name, {"form": form, "breakdown_request": breakdown_request})
 



class ServiceProviderDashboardView(View):
    template_name = "provider_dashboard.html"

    def get(self, request, *args, **kwargs):
        # Fetch all breakdown requests except 'pending', 'cancelled', and 'completed' statuses for the current user
        qs = BreakdownRequest.objects.filter(
            service_provider=request.user
        ).exclude(status__in=['delivered','cancelled']).order_by('-created_date')

        breakdown_data = []
        for request_instance in qs:
            try:
                # Group services under vehicle types
                grouped_services = {
                    'two_wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
                    'four_wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
                    'others': request_instance.service_types.filter(vehicle_type='others'),
                }
            except ServiceType.DoesNotExist:
                grouped_services = None

            breakdown_data.append({
                "request": request_instance,
                "grouped_services": grouped_services,
                "status": request_instance.get_status_display(),  # Display the readable status
            })

        context = {
            "data": breakdown_data,
        }
        return render(request, self.template_name, context)

from django.http import Http404 

class SetPaymentAmountView(View):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')  # Retrieve the primary key from URL
        breakdown_request = BreakdownRequest.objects.filter(pk=pk).first()

        if not breakdown_request:
            raise Http404("Breakdown Request not found.")

        # Check if the service provider is the logged-in user
        if breakdown_request.service_provider != request.user:
            raise Http404("You are not authorized to access this request.")

        # Check if the BreakdownRequest status is 'completed'
        if breakdown_request.status != 'completed':
            return render(request, 'set_payment_amount.html', {
                'breakdown_request': breakdown_request,
                'error': "Payment can only be initiated after the request is completed.",
            })

        # Check for existing Payment; do not create if it doesn't exist
        try:
            payment = Payment.objects.get(breakdown_request=breakdown_request)
        except Payment.DoesNotExist:
            payment = None  # Set to None if it doesn't exist

        return render(request, 'set_payment_amount.html', {
            'breakdown_request': breakdown_request,
            'payment': payment,
        })

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')  # Retrieve the primary key from URL
        breakdown_request = BreakdownRequest.objects.filter(pk=pk).first()

        if not breakdown_request:
            raise Http404("Breakdown Request not found.")

        if breakdown_request.service_provider != request.user:
            raise Http404("You are not authorized to update this request.")

        if breakdown_request.status != 'completed':
            return render(request, 'set_payment_amount.html', {
                'breakdown_request': breakdown_request,
                'error': "Payment can only be initiated after the request is completed.",
            })

        # Get the amount from the POST data
        amount = request.POST.get('amount')
        if not amount or int(amount) <= 0:
            return render(request, 'set_payment_amount.html', {
                'breakdown_request': breakdown_request,
                'error': "Invalid amount provided.",
            })

        # Fetch or create the Payment object
        payment, created = Payment.objects.get_or_create(
            breakdown_request=breakdown_request,
            defaults={'amount': int(amount)}  # Default payment_method
        )

        if not created:  # Update the amount if Payment already exists
            payment.amount = int(amount)
            payment.save()

        return redirect('provider-dashboard')  # Redirect to the next page


class CustomerDashboardView(View):
    template_name = "customer_dashboard.html"

    def get(self, request, *args, **kwargs):
        # Fetch all breakdown requests except 'pending', 'cancelled', and 'completed' statuses for the current user
        qs = BreakdownRequest.objects.filter(
            customer=request.user
        ).exclude(status__in=['delivered']).order_by('-created_date')

        breakdown_data = []
        for request_instance in qs:
            try:
                # Group services under vehicle types
                grouped_services = {
                    'two_wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
                    'four_wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
                    'others': request_instance.service_types.filter(vehicle_type='others'),
                }
            except ServiceType.DoesNotExist:
                grouped_services = None

            breakdown_data.append({
                "request": request_instance,
                "grouped_services": grouped_services,
                "status": request_instance.get_status_display(),  # Display the readable status
            })

        context = {
            "data": breakdown_data,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Handle the accept or cancel action
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

        # Fetch and update the status of the breakdown request
        breakdown_request = BreakdownRequest.objects.filter(id=request_id).first()
        if breakdown_request:
            if action == "cancel":
                breakdown_request.status = "cancelled"
                breakdown_request.save()

        # Redirect back to the updated view
        return self.get(request, *args, **kwargs)

import razorpay

import json

class CustomerPaymentView(View):
    template_name = 'customer_payment.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        breakdown_request = get_object_or_404(BreakdownRequest, pk=pk)
        payment = Payment.objects.filter(breakdown_request=breakdown_request).first()

        if not payment:
            raise Http404("Payment not found for this Breakdown Request.")

        return render(request, self.template_name, {
            'breakdown_request': breakdown_request,
            'payment': payment
        })

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        breakdown_request = get_object_or_404(BreakdownRequest, pk=pk)
        payment = Payment.objects.get(breakdown_request=breakdown_request)

        # Prevent further payments if already completed
        if payment.payment_status == 'completed':
            return JsonResponse({"error": "Payment has already been completed."}, status=400)

        # Parse JSON data if sent via fetch
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        payment_method = data.get('payment_method')

        if payment_method == 'razorpay':
            client = razorpay.Client(auth=(config('KEY_ID'), config('KEY_SECRET')))
            razorpay_order = client.order.create({
                "amount": payment.amount * 100,  # Convert to paisa
                "currency": "INR",
                "receipt": f"order_rcptid_{payment.id}",
            })

            payment.payment_method = 'razorpay'
            payment.razorpay_order_id = razorpay_order['id']
            payment.save()

            return JsonResponse({
                "key": config('KEY_ID'),
                "amount": razorpay_order['amount'],
                "order_id": razorpay_order['id'],
                "name": "Your Company Name",
                "description": "Service Payment",
            })

        elif payment_method == 'cod':
            if payment.payment_status != 'completed':  # Double-check for cod payments
                payment.payment_method = 'cod'
                payment.payment_status = 'completed'
                payment.save()
                return redirect('customer-dashboard')

        return JsonResponse({"error": "Invalid payment method"}, status=400)




class PaymentVerificationView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Parse JSON body
            body = json.loads(request.body)

            razorpay_order_id = body.get('razorpay_order_id')
            razorpay_payment_id = body.get('razorpay_payment_id')
            razorpay_signature = body.get('razorpay_signature')

            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                return JsonResponse({"error": "Incomplete Razorpay parameters."}, status=400)

            # Verify Razorpay signature
            client = razorpay.Client(auth=(config('KEY_ID'), config('KEY_SECRET')))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Update payment record
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.payment_status = 'completed'
            payment.save()

            return JsonResponse({"message": "Payment verified successfully."})
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment record not found."}, status=404)
        except razorpay.errors.SignatureVerificationError as e:
            return JsonResponse({"error": "Signature verification failed.", "details": str(e)}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            return JsonResponse({"error": "An unexpected error occurred.", "details": str(e)}, status=400)


class ServiceProviderHistoryView(View):
    template_name = "provider_History.html"

    def get(self, request, *args, **kwargs):
        
        qs = BreakdownRequest.objects.filter(
            service_provider=request.user,status='delivered'
        ).order_by('-created_date')

        return render(request,self.template_name,{"data":qs})


class CustomerHistoryView(View):
    template_name = "customer_History.html"

    def get(self, request, *args, **kwargs):
        
        qs = BreakdownRequest.objects.filter(
            customer=request.user,status='delivered'
        ).order_by('-created_date')

        return render(request,self.template_name,{"data":qs})
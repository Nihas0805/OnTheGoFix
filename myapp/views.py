from django.shortcuts import render,redirect,get_object_or_404

from django.views.generic import View,FormView

from myapp.forms import SignUpForm,SignInForm,ServiceProviderProfileForm,BreakdownRequestCreateForm,CustomerProfileForm,BreakdownRequestUpdateForm,RatingForm,PasswordResetForm

from django.core.mail import send_mail

from django.contrib import messages

from twilio.rest import Client

from myapp.models import User,BreakdownRequest,ServiceProviderProfile,BreakdownRequest,CustomerProfile,ServiceType,Payment,Rating

from django.contrib.auth import authenticate,login,logout

from django.urls import reverse_lazy

from django.db.models import Case, When, Value, IntegerField

from decouple import config

from django.http import JsonResponse

from django.contrib import messages

from django.utils.decorators import method_decorator

from django.views.decorators.cache import never_cache

from myapp.decorators import signin_required

from django.db.models import Count

from django.db.models import Q 



decs=[signin_required,never_cache]




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

from django.shortcuts import render

def landing_page(request):
    

    # Render the template with the services list
    return render(request, 'landing.html')



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




@method_decorator(decs,name="dispatch")

class CustomerIndexView(View):
    template_name = "customer_index.html"

    def get(self, request, *args, **kwargs):
        
        search_keyword = request.GET.get("search", "").strip()

        qs = ServiceProviderProfile.objects.prefetch_related('service_types').all().order_by('-availability_status')

        if search_keyword:
            qs = qs.filter(
                Q(user__username__icontains=search_keyword) |
                Q(address__icontains=search_keyword) |
                Q(service_types__name__icontains=search_keyword) |
                Q(service_types__vehicle_type__icontains=search_keyword)
            ).distinct()

        vehicle_types = ServiceType.objects.values_list('vehicle_type', flat=True).distinct()

        data = {
            "providers": qs,
            "vehicle_types": vehicle_types,
            "search_keyword": search_keyword,  
        }
        return render(request, self.template_name, data)


        
@method_decorator(decs,name="dispatch")
class ProviderIndexView(View):
    template_name = "provider_index.html"

    def get(self, request, *args, **kwargs):

        search_keyword = request.GET.get("search", "").strip()

        qs = BreakdownRequest.objects.filter(service_provider=request.user, status='pending').order_by('created_date')
        
        if search_keyword:
            qs = qs.filter(
                Q(service_types__name__icontains=search_keyword) |
                Q(service_types__vehicle_type__icontains=search_keyword)
            ).distinct()

        breakdown_data = []  

        for requests in qs:
            breakdown_data.append(
                {
                    "request": requests,
                    "grouped_services": {
                        'Two Wheeler': requests.service_types.filter(vehicle_type='two_wheeler'),
                        'Four Wheeler': requests.service_types.filter(vehicle_type='four_wheeler'),
                        'Others': requests.service_types.filter(vehicle_type='others'),
                    }
                }
            )

        return render(request, self.template_name, {"data": breakdown_data,"search_keyword": search_keyword, })



    def post(self, request, *args, **kwargs):
        
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

       
        breakdown_request = BreakdownRequest.objects.filter(id=request_id).first()
        if breakdown_request:
            if action == "accept":
                breakdown_request.status = "accepted"
                messages.success(request,"Service Accepted")
            elif action == "cancel":
                breakdown_request.status = "cancelled"
                messages.error(request,"Service Rejected")
            breakdown_request.save()

        
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


@method_decorator(decs,name="dispatch")
class LogoutView(View):
    
    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect("signin")
    



@method_decorator(decs,name="dispatch")
class ServiceProviderProfileEditView(View):

    template_name = "provider_profile_edit.html"
    form_class = ServiceProviderProfileForm

    def get(self, request, *args, **kwargs):
        
        profile_object = ServiceProviderProfile.objects.get(user=request.user)
        form_instance = self.form_class(instance=profile_object, user=request.user)
        return render(request, self.template_name, {"form": form_instance})

    def post(self, request, *args, **kwargs):
        
        profile_object = ServiceProviderProfile.objects.get(user=request.user)
        
        
        form_instance = self.form_class(request.POST, request.FILES, instance=profile_object, user=request.user)
        
        if form_instance.is_valid():
            profile = form_instance.save(commit=False)
            profile.user = request.user  
            profile.save()
            form_instance.save_m2m() 
            messages.success(request,"Updated Successfully")
            
            
            return redirect("provider-profile")
        else:
            messages.error(request,"Error Updating")

        return render(request, self.template_name, {"form": form_instance})





@method_decorator(decs,name="dispatch")
class ProviderProfileView(View):

    template_name = "provider_profile.html"

    def get(self, request, *args, **kwargs):
    
        profile = ServiceProviderProfile.objects.prefetch_related('service_types').filter(user=request.user).first()

        
        grouped_services = {
            'Two Wheeler': profile.service_types.filter(vehicle_type='two_wheeler'),
            'Four Wheeler': profile.service_types.filter(vehicle_type='four_wheeler'),
            'Others': profile.service_types.filter(vehicle_type='others'),
        }

        
        return render(request, self.template_name, {"profile": profile,"grouped_services": grouped_services,})


class CustomerIndexDetailView(View):

    template_name = "customer_index_detail_view.html"

    def get(self, request, *args, **kwargs):

        id=kwargs.get("pk")
    
        qs = ServiceProviderProfile.objects.prefetch_related('service_types').filter(id=id).first()

        
        grouped_services = {
            'Two Wheeler': qs.service_types.filter(vehicle_type='two_wheeler'),
            'Four Wheeler': qs.service_types.filter(vehicle_type='four_wheeler'),
            'Others': qs.service_types.filter(vehicle_type='others'),
        }

        
        return render(request, self.template_name, {"data": qs,"grouped_services": grouped_services,})




@method_decorator(decs,name="dispatch")
class BreakdownRequestCreateView(View):

    template_name = 'breakdownrequest_create.html'

    form_class =BreakdownRequestCreateForm

    def get(self, request, *args, **kwargs):
        service_provider_id = kwargs.get('service_provider_id')
        

        service_provider = ServiceProviderProfile.objects.filter(id=service_provider_id).first()
        

        
        form_instance = self.form_class(service_provider=service_provider, user=request.user)

        return render(request, self.template_name, {
            'form': form_instance,
            'service_provider': service_provider,
        })

    def post(self, request, *args, **kwargs):
        service_provider_id = kwargs.get('service_provider_id')

        service_provider = ServiceProviderProfile.objects.filter(id=service_provider_id).first()
        
        
        form_instance = self.form_class(request.POST, request.FILES, service_provider=service_provider, user=request.user)

        if form_instance.is_valid():
            
            breakdown_request = form_instance.save(commit=False)
            breakdown_request.customer = request.user
            breakdown_request.service_provider = service_provider.user
            breakdown_request.save()
            messages.success(request, "Request sent")
            form_instance.save_m2m()

            customer_address = form_instance.cleaned_data.get('customer_address')
            if request.user.customer_profile:
                request.user.customer_profile.address = customer_address
                request.user.customer_profile.save()

            return redirect('customer-index')

        
        return render(request, self.template_name, {
            'form': form_instance,
            'service_provider': service_provider,
        })

@method_decorator(decs,name="dispatch")
class ProviderBreakdownRequestDetailView(View):
    template_name = "breakdownrequest_provider_detail.html"

    def get(self, request, *args, **kwargs):
        id = kwargs.get("pk")

        request_instance = BreakdownRequest.objects.get(id=id)
        
        payment = Payment.objects.filter(breakdown_request=request_instance).first()

        grouped_services = {
            'Two Wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
            'Four Wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
            'Others': request_instance.service_types.filter(vehicle_type='others'),
        }

        
        context = {
            "request": request_instance,
            "grouped_services": grouped_services,
            "payment": payment,  
        }
        return render(request, self.template_name, context)



@method_decorator(decs,name="dispatch")
class CustomerBreakdownRequestDetailView(View):
    template_name = "breakdownrequest_customer_detail.html"

    def get(self, request, *args, **kwargs):
        id = kwargs.get("pk")

    
        request_instance = BreakdownRequest.objects.get(id=id)
       

        
        payment = Payment.objects.filter(breakdown_request=request_instance).first()

        
        grouped_services = {
            'Two Wheeler': request_instance.service_types.filter(vehicle_type='two_wheeler'),
            'Four Wheeler': request_instance.service_types.filter(vehicle_type='four_wheeler'),
            'Others': request_instance.service_types.filter(vehicle_type='others'),
        }

        context = {
            "request": request_instance,
            "grouped_services": grouped_services,
            "payment": payment,  
        }
        return render(request, self.template_name, context)         


@method_decorator(decs,name="dispatch")
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
            messages.success(request,"Updated Successfully")
            return redirect("customer-profile")

        return render(request, self.template_name, {"form": form_instance})



@method_decorator(decs,name="dispatch")
class CustomerProfileListView(View):
    
    template_name="customer_profile.html"

    def get(self,request,*args,**kwargs):

        qs=CustomerProfile.objects.get(user=request.user)

        return render(request,self.template_name,{"data":qs})



from django.utils.timezone import now


@method_decorator(decs,name="dispatch")
class BreakdownRequestUpdateView(View):
    template_name = "breakdownrequest_edit.html"

    form_class=BreakdownRequestUpdateForm

    def get(self, request, *args, **kwargs):
        
        id = kwargs.get('pk')
    
        breakdown_request = BreakdownRequest.objects.get(id=id)
        
        form_instance = self.form_class(instance=breakdown_request)

        return render(request, self.template_name, {"form": form_instance, "breakdown_request": breakdown_request})

    def post(self, request, *args, **kwargs):
    
        id = kwargs.get('pk')
        
        breakdown_request = BreakdownRequest.objects.get(id=id)

        form_instance = self.form_class(request.POST, request.FILES, instance=breakdown_request)

        if form_instance.is_valid():
            updated_request = form_instance.save(commit=False)

            updated_request.image = breakdown_request.image
            updated_request.customer = breakdown_request.customer
            updated_request.service_provider = breakdown_request.service_provider
            updated_request.description = breakdown_request.description
            updated_request.latitude = breakdown_request.latitude
            updated_request.longitude = breakdown_request.longitude

            
            updated_request.status = form_instance.cleaned_data["status"]
            updated_request.estimated_date = form_instance.cleaned_data["estimated_date"]

            
            if 'take_action' in request.POST:
                updated_request.status = 'accepted'
            elif 'cancel' in request.POST:
                updated_request.status = 'cancelled'

            
            if updated_request.status == 'delivered':
                updated_request.completed_at = now()
            else:
                updated_request.completed_at = None

            updated_request.save()
            messages.success(request, "Updated Successfully")
            return redirect('provider-dashboard')  
        return render(request, self.template_name, {"form": form_instance,"breakdown_request": breakdown_request,"form_errors": form.errors, })


@method_decorator(decs,name="dispatch")
class ServiceProviderDashboardView(View):
    template_name = "provider_dashboard.html"

    def get(self, request, *args, **kwargs):
        search_keyword = request.GET.get("search", "").strip()
        selected_status = request.GET.get("status", "all")

        if search_keyword:
            qs = BreakdownRequest.objects.filter(service_provider=request.user).filter(
                Q(customer__username__icontains=search_keyword) |
                Q(service_types__name__icontains=search_keyword) |
                Q(service_types__vehicle_type__icontains=search_keyword)
            ).distinct()
        else:
            if selected_status == "all":
                qs = BreakdownRequest.objects.filter(service_provider=request.user).exclude(
                    status__in=['delivered', 'pending', 'cancelled']
                ).order_by('-created_date')
            else:
                qs = BreakdownRequest.objects.filter(
                    status=selected_status, service_provider=request.user
                ).order_by('-created_date')

        # Counts by Status
        breakdown_counts = BreakdownRequest.objects.filter(service_provider=request.user).exclude(
            status__in=['delivered', 'pending', 'cancelled']
        ).values('status').annotate(count=Count('id'))

        # Prepare breakdown data
        breakdown_data = []
        for requests in qs:
            breakdown_data.append(
                {
                    "request": requests,
                    "grouped_services": {
                        'two_wheeler': requests.service_types.filter(vehicle_type='two_wheeler'),
                        'four_wheeler': requests.service_types.filter(vehicle_type='four_wheeler'),
                        'others': requests.service_types.filter(vehicle_type='others'),
                    },
                    "status": requests.get_status_display(),
                }
            )

        # Total count
        total_requests = sum(item['count'] for item in breakdown_counts)

        return render(
            request,
            self.template_name,
            {
                "data": breakdown_data,
                "selected": selected_status,
                "search_keyword": search_keyword,
                "total_requests": total_requests,
                "breakdown_counts": breakdown_counts,
            },
        )




from django.http import Http404,HttpResponse,HttpResponseNotFound

@method_decorator(decs,name="dispatch")
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
            messages.success(request,"Payment initiated successfully")

        return redirect('provider-dashboard')  # Redirect to the next page


@method_decorator(decs,name="dispatch")
class CustomerDashboardView(View):
    template_name = "customer_dashboard.html"

    def get(self, request, *args, **kwargs):
        
        search_keyword = request.GET.get("search", "").strip()
        selected_status = request.GET.get("status", "all")

        if search_keyword:
            
            qs = BreakdownRequest.objects.filter(customer=request.user).filter(
                Q(service_provider__username__icontains=search_keyword) |
                Q(service_types__name__icontains=search_keyword) |
                Q(service_types__vehicle_type__icontains=search_keyword)
            ).distinct()
        else:    
            if selected_status == "all":
                qs = BreakdownRequest.objects.filter(customer=request.user).exclude(status__in=["delivered", "cancelled"]).order_by("-created_date")
            else:
                qs = BreakdownRequest.objects.filter(status=selected_status, customer=request.user).order_by("-created_date")

        
        breakdown_data = []
        for requests in qs:
            breakdown_data.append(
                {
                    "request": requests,
                    "grouped_services": {
                        'two_wheeler': requests.service_types.filter(vehicle_type='two_wheeler'),
                        'four_wheeler': requests.service_types.filter(vehicle_type='four_wheeler'),
                        'others': requests.service_types.filter(vehicle_type='others'),
                    },
                    "status": requests.get_status_display(),
                }
            )

        return render(request,self.template_name,{"data": breakdown_data,"selected": selected_status,"search_keyword": search_keyword,},)


    def post(self, request, *args, **kwargs):
        
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

        
        breakdown_request = BreakdownRequest.objects.filter(id=request_id).first()
        if breakdown_request:
            if action == "cancel":
                breakdown_request.status = "cancelled"
                breakdown_request.save()
                messages.error(request,"Cancelled")

        
        return self.get(request, *args, **kwargs)


import razorpay

import json

@method_decorator(decs,name="dispatch")
class CustomerPaymentView(View):
    template_name = 'customer_payment.html'

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        breakdown_request = get_object_or_404(BreakdownRequest, pk=pk)
        payment = Payment.objects.filter(breakdown_request=breakdown_request).first()

        return render(request, self.template_name, {'breakdown_request': breakdown_request,'payment': payment})

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        breakdown_request = get_object_or_404(BreakdownRequest, pk=pk)
        payment = Payment.objects.get(breakdown_request=breakdown_request)

    
        if payment.payment_status == 'completed':
            return JsonResponse({"error": "Payment has already been completed."}, status=400)

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
            messages.success(request,"Payment Successfully Completed")


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
                messages.success(request,"Payment Successfully Completed")

                
                return redirect('customer-dashboard')

        return JsonResponse({"error": "Invalid payment method"}, status=400)



@method_decorator(decs,name="dispatch")
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



@method_decorator(decs,name="dispatch")
class ServiceProviderHistoryView(View):
    template_name = "provider_History.html"

    def get(self, request, *args, **kwargs):

        
        qs = BreakdownRequest.objects.filter(service_provider=request.user,status='delivered').select_related('payment').order_by('-created_date')

        return render(request,self.template_name,{"data":qs})


@method_decorator(decs,name="dispatch")
class CustomerHistoryView(View):
    template_name = "customer_History.html"

    def get(self, request, *args, **kwargs):

        qs = BreakdownRequest.objects.filter(customer=request.user, status='delivered').select_related('payment').order_by('-created_date')

        return render(request, self.template_name, {"data": qs})



@method_decorator(decs,name="dispatch")
class CreateRatingView(View):

    form_class = RatingForm
    def get(self, request, *args, **kwargs):
        id = kwargs.get('pk')

        breakdown_request = BreakdownRequest.objects.get(id=id)
    
        form_instance = self.form_class

        return render(request, 'create_rating.html', {'form': form_instance,'service_provider': breakdown_request.service_provider,'breakdown_request': breakdown_request,})

    def post(self, request, *args, **kwargs):
        id = kwargs.get('pk')

        breakdown_request = BreakdownRequest.objects.get(id=id)
        
        
        form_instance = RatingForm(request.POST)
        if form_instance.is_valid():
            # Save the rating
            rating = form_instance.save(commit=False)
            rating.breakdown_request = breakdown_request
            rating.service_provider = breakdown_request.service_provider
            rating.save()
            messages.success(request,"Service has been rated")

            service_provider_profile = ServiceProviderProfile.objects.get(user=breakdown_request.service_provider)
            service_provider_profile.update_rating()
            
            return redirect('customer-history')  # Replace with your desired redirect path
        else:
            return render(request, 'create_rating.html', {'form': form_instance,'service_provider': breakdown_request.service_provider,'breakdown_request': breakdown_request, })




@method_decorator(decs,name="dispatch")
class RatingListView(View):
    def get(self, request, *args, **kwargs):
        service_provider_id = kwargs.get('pk')  

        service_provider = ServiceProviderProfile.objects.get(user_id=service_provider_id)  
      
        ratings = Rating.objects.filter(service_provider_id=service_provider_id).select_related('breakdown_request__customer')
        
        return render(request, 'rating_list.html', {'service_provider': service_provider,'ratings': ratings,})


@method_decorator(decs,name="dispatch")
class PasswordResestView(View):

    template_name="password_reset.html"

    form_class=PasswordResetForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):

        form_instance=self.form_class(request.POST)

        if form_instance.is_valid():

            username=form_instance.cleaned_data.get("username")

            email=form_instance.cleaned_data.get("email")

            password1=form_instance.cleaned_data.get("password1")

            password2=form_instance.cleaned_data.get("password2")

            print(username,email,password1,password2)

            try:
                assert password1==password2,"password mismatch"

                user_object=User.objects.get(username=username,email=email)

                user_object.set_password(password2)

                user_object.save()

                return redirect('signin')

            except Exception as e:

                messages.error(request,f"{e}")

                return render(request,self.template_name,{"form":form_instance})

        return render(request,self.template_name,{"form":form_instance})

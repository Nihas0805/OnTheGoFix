from django.shortcuts import render,redirect

from django.views.generic import View,FormView

from myapp.forms import SignUpForm,SignInForm

from django.core.mail import send_mail

from django.contrib import messages

from twilio.rest import Client

from myapp.models import User,BreakdownRequest

from django.contrib.auth import authenticate,login

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

            return redirect("signup")

        except:

            messages.error(request,"Invalid otp")

            return render(request,self.template_name)

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy

class CustomerIndexView(View):

    template_name="customer_index.html"

    def get(self,request,*args,**kwargs):

        qs=BreakdownRequest.objects.all()

        return render(request,self.template_name,{"data":qs})

class ProviderIndexView(View):

    template_name="provider_index.html"

    def get(self,request,*args,**kwargs):

        qs=BreakdownRequest.objects.filter(service_provider=request.user)

        return render(request,self.template_name,{"data":qs})

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
    



 

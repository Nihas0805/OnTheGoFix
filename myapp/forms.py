from django import forms

from myapp.models import User

from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):

    class Meta:

        model=User

        fields= ['username', 'email', 'role', 'phone_number', 'password1', 'password2']

class SignInForm(forms.Form):

    username=forms.CharField(max_length=200)

    password=forms.CharField(widget=forms.PasswordInput())

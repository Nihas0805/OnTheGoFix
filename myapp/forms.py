from django import forms

from myapp.models import User,ServiceProviderProfile,ServiceType,BreakdownRequest,CustomerProfile,Rating

from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = None  # Remove help text
            field.label = ''  # Remove labels, if desired
            # Apply Bootstrap 'form-control' class to each field
            field.widget.attrs.update({'class': 'form-control'})
          
        

class SignInForm(forms.Form):

    username=forms.CharField(max_length=200)

    password=forms.CharField(widget=forms.PasswordInput())




class ServiceProviderProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Name'
    )

    service_types = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Service Types",
    )

    class Meta:
        model = ServiceProviderProfile
        fields = ['service_types', 'address', 'availability_status', 'profile_picture']
        widgets = {
            'availability_status': forms.Select(choices=[(True, 'Available'), (False, 'Not Available')]),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['username'].initial = user.username

        grouped_service_types = {}
        for service in ServiceType.objects.all():
            vehicle_type_label = dict(ServiceType.vehicle_type_choices).get(service.vehicle_type, "Others")
            grouped_service_types.setdefault(vehicle_type_label, []).append((service.id, service.name))

        self.fields['service_types'].choices = [(group, services) for group, services in grouped_service_types.items()]


    




class BreakdownRequestCreateForm(forms.ModelForm):
    
    service_provider_username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=False,
        label="Service Provider"
    )
    customer_address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label="Address"
    )
    vehicle_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label="Vehicle Model"
    )

    
    service_types = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Service Types"
    )

    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = BreakdownRequest
        fields = ['description', 'image', 'latitude', 'longitude', 'service_types','vehicle_name']

    def __init__(self, *args, **kwargs):
        service_provider = kwargs.pop('service_provider', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        
        if service_provider:
            self.fields['service_types'].queryset = service_provider.service_types.all()

       
        if service_provider and service_provider.user:
            self.fields['service_provider_username'].initial = service_provider.user.username

        if user and hasattr(user, 'customer_profile'):
            self.fields['customer_address'].initial = user.customer_profile.address

        
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['image'].widget.attrs.update({'class': 'form-control'})

        self.grouped_service_types = self.group_service_types_by_vehicle_type(service_provider)

    def group_service_types_by_vehicle_type(self, service_provider):
        grouped = {
            'two_wheeler': [],
            'four_wheeler': [],
            'others': []
        }
        if service_provider:
            for service in service_provider.service_types.all():
                grouped[service.vehicle_type].append(service)
        return grouped







class CustomerProfileForm(forms.ModelForm):
    
    username = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Name'
    )
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'form-control'}), 
        label='E-mail'
    )
    phone_number = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Phone Number'
    )
    
    address = forms.CharField(
        max_length=200, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Address'
    )

    class Meta:
        model = CustomerProfile
        fields = ['address']  

    def __init__(self, *args, **kwargs):
        
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
           
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['phone_number'].initial = user.phone_number





class BreakdownRequestUpdateForm(forms.ModelForm):
    service_types_display = forms.CharField(
        label="Service Types",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "readonly": "readonly"})
    )

    class Meta:
        model = BreakdownRequest
        fields = [
            
            "status",
            
            "estimated_date",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),  # Editable
            "estimated_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        if self.instance and self.instance.pk:
            service_types_display_text = "\n".join(
                f"{st.get_vehicle_type_display()} : {st.name}"
                for st in self.instance.service_types.all()
            )
            self.fields["service_types_display"].initial = service_types_display_text


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'review']


class PasswordResetForm(forms.Form):

    username=forms.CharField()

    email=forms.EmailField()

    password1=forms.CharField()

    password2=forms.CharField()

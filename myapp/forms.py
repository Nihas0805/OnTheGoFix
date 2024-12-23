from django import forms

from myapp.models import User,ServiceProviderProfile,ServiceType,BreakdownRequest,CustomerProfile,Rating

from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):

    class Meta:

        model=User

        fields= ['username', 'email', 'role', 'phone_number', 'password1', 'password2']

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

        # Populate the 'username' field with the user's name
        if user:
            self.fields['username'].initial = user.username

        # Group Service Types by vehicle_type
        grouped_service_types = {}
        for service in ServiceType.objects.all():
            vehicle_type_label = dict(ServiceType.vehicle_type_choices).get(service.vehicle_type, "Others")
            grouped_service_types.setdefault(vehicle_type_label, []).append((service.id, service.name))

        # Set choices for service_types
        self.fields['service_types'].choices = [(group, services) for group, services in grouped_service_types.items()]


    




class BreakdownRequestCreateForm(forms.ModelForm):
    # Service Provider Username (Read-Only Field)
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

    # Dynamically group service types by vehicle type
    service_types = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Service Types"
    )

    latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = BreakdownRequest
        fields = ['description', 'image', 'latitude', 'longitude', 'service_types']

    def __init__(self, *args, **kwargs):
        service_provider = kwargs.pop('service_provider', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set service types based on the selected service provider
        if service_provider:
            self.fields['service_types'].queryset = service_provider.service_types.all()

        # Prepopulate the service provider username and customer address
        if service_provider and service_provider.user:
            self.fields['service_provider_username'].initial = service_provider.user.username

        if user and hasattr(user, 'customer_profile'):
            self.fields['customer_address'].initial = user.customer_profile.address

        # Additional widget styling
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['image'].widget.attrs.update({'class': 'form-control'})

        # Prepare grouped service types for display
        self.grouped_service_types = self.group_service_types_by_vehicle_type(service_provider)

    def group_service_types_by_vehicle_type(self, service_provider):
        """
        Group the service types by vehicle type for display in the form.
        """
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
    # Username and email are read-only, but initialized with current user's values
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
    
    address = forms.CharField(
        max_length=200, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Address'
    )

    class Meta:
        model = CustomerProfile
        fields = ['address']  # Only 'address' is editable

    def __init__(self, *args, **kwargs):
        # Pop 'user' from kwargs, if passed, to initialize username/email fields
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Initialize 'username' and 'email' with the user's data
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email





class BreakdownRequestUpdateForm(forms.ModelForm):
    service_types_display = forms.CharField(
        label="Service Types",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "readonly": "readonly"})
    )

    class Meta:
        model = BreakdownRequest
        fields = [
            "customer",
            "service_provider",
            "description",
            "image",
            "status",
            "latitude",
            "longitude",
            "estimated_date",
        ]
        widgets = {
            "customer": forms.HiddenInput(),  # Readonly Text Input
            "status": forms.Select(attrs={"class": "form-control"}),  # Editable
            "description": forms.HiddenInput(),  # Hidden
            "image": forms.HiddenInput(),  # Hidden
            "service_provider": forms.HiddenInput(),  # Hidden
            "latitude": forms.HiddenInput(),  # Hidden
            "longitude": forms.HiddenInput(),  # Hidden
            "estimated_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Combine vehicle type and service type for display
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

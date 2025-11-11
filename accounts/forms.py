from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class SignupForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Username',
            'id': 'username',
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Email',
            'id': 'email',
        }),
        label="Email"
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Password',
            'id': 'password1',
        }),
        label="Password",
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'id': 'password2',
        }),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove all password validators
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2
    
    def _post_clean(self):
        # Override to skip Django's password validation
        super(UserCreationForm, self)._post_clean()




class ActivationForm(forms.Form):
    code = forms.CharField(max_length=8)


from django import forms
from .models import Profile
from django.contrib.auth.models import User
from orders.models import PickupStation

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Modify the shipping_address to use ModelChoiceField to create a dropdown
    shipping_address = forms.ModelChoiceField(
        queryset=PickupStation.objects.all(),  # All available PickupStation objects
        required=False,  # Make this field optional
        widget=forms.Select(attrs={'class': 'form-control'}),  # Use Select widget for dropdown
        empty_label="Select a Pickup Station"  # You can set a custom label for the default empty option
    )
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    payment_method = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Profile
        fields = ['image', 'first_name', 'last_name', 'email', 'bio', 'phone_number', 'shipping_address', 'date_of_birth', 'gender', 'payment_method']

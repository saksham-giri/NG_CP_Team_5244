from django import forms
from django.contrib.auth import get_user_model

from .models import BuyerProfile, ScrapListing, SellerProfile


class LoginForm(forms.Form):
    username_or_email = forms.CharField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)


class BuyerRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    full_name = forms.CharField(max_length=255)
    business_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        if user_model.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email


class SellerRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    full_name = forms.CharField(max_length=255)
    business_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    pickup_address = forms.CharField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        if user_model.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email


class SellerDashboardListingForm(forms.ModelForm):
    class Meta:
        model = ScrapListing
        fields = ["category", "description", "price_per_kg", "quantity_kg", "location"]
        labels = {
            "price_per_kg": "Asking Price (₹ per kg)",
            "quantity_kg": "Weight (kg)",
            "location": "Address",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = True
        self.fields["location"].required = True


def create_user_and_buyer_profile(cleaned_data):
    user_model = get_user_model()
    full_name = cleaned_data["full_name"].strip()
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    user = user_model.objects.create_user(
        username=cleaned_data["username"].strip(),
        email=cleaned_data["email"].strip().lower(),
        password=cleaned_data["password"],
        first_name=first_name,
        last_name=last_name,
    )
    BuyerProfile.objects.create(
        user=user,
        business_name=cleaned_data["business_name"].strip(),
        phone_number=cleaned_data["phone_number"].strip(),
        address=cleaned_data.get("address", "").strip(),
    )
    return user


def create_user_and_seller_profile(cleaned_data):
    user_model = get_user_model()
    full_name = cleaned_data["full_name"].strip()
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    user = user_model.objects.create_user(
        username=cleaned_data["username"].strip(),
        email=cleaned_data["email"].strip().lower(),
        password=cleaned_data["password"],
        first_name=first_name,
        last_name=last_name,
    )
    SellerProfile.objects.create(
        user=user,
        business_name=cleaned_data["business_name"].strip(),
        phone_number=cleaned_data["phone_number"].strip(),
        pickup_address=cleaned_data.get("pickup_address", "").strip(),
    )
    return user

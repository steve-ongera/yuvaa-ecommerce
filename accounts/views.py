from django.shortcuts import render , redirect
from .forms import *
from django.contrib.auth.models import User
from .models import Profile
from django.core.mail import send_mail
from django.contrib.auth import logout
from django.contrib.auth import authenticate , login
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    next_url = request.GET.get("next", "/")  # Get the 'next' parameter from GET request
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in successfully.")
            next_url = request.POST.get("next", "/")  # Get the 'next' parameter from the form submission
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")
    
    # Pass the next_url to the template context
    return render(request, "registration/login.html", {"next": next_url})







def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            
            # Create user object but don't save it yet
            user = form.save(commit=False)
            user.is_active = True  # Changed to True - user is active immediately
            user.save()
            
            # Create or update the profile associated with this user
            profile = Profile.objects.get(user__username=username)
            
            # Send welcome email (optional - you can keep or remove this)
            send_mail(
                "Welcome to Your Account",
                f"Welcome {username}! Your account has been activated. You can now login.",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
                
            # Redirect directly to login instead of activation page
            messages.success(request, "Registration successful! Welcome aboard.")
            return redirect('/accounts/login')
            
    else:
        form = SignupForm()
    
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('/')

#this part of the view has already be implimented on the signup view automatically 
def activate(request, username):
    # Fetch profile of the user
    profile = Profile.objects.get(user__username=username)

    if request.method == 'POST':
        form = ActivationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            # Check if the entered code matches the code stored in the profile
            if code == profile.code:
                # Clear the activation code after successful activation
                profile.code = ''

                # Activate the user account
                user = User.objects.get(username=profile.user.username)
                user.is_active = True  # Correct the field name to 'is_active'
                user.save()

                # Save the profile
                profile.save()

                # Redirect to login page
                return redirect('/accounts/login')
            else:
                # If the code doesn't match, you could add an error message
                form.add_error('code', 'Invalid activation code.')
    else:
        form = ActivationForm()

    return render(request, 'registration/activate.html', {'form': form})


@login_required
def view_profile(request):
    # Get the profile of the logged-in user
    profile = Profile.objects.get(user=request.user)
    
    return render(request, 'registration/view_profile.html', {'profile': profile})

@login_required
def update_profile(request):
    profile = Profile.objects.get(user=request.user)
    user = request.user  # Get the User object

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            # Update user fields (first_name, last_name, email)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # Save the updated profile
            form.save()
            return redirect('accounts:view_profile')  # Redirect to the profile page or any other page
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'registration/update_profile.html', {'form': form})


# reset password views

from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

User = get_user_model()

def password_reset_request(request):
    """View to handle password reset requests and send verification emails"""
    if request.method == "POST":
        email = request.POST.get("email", "")
        
        # Check if the email exists in the database
        try:
            user = User.objects.get(email=email)
            
            # Generate a token and uid for the user
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Build the reset URL
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Render the email template
            email_subject = "Password Reset Request"
            email_body = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': request.get_host(),
            })
            
            # Send the email
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, "A password reset link has been sent to your email address.")
            return redirect('accounts:password_reset_done')
        
        except User.DoesNotExist:
            # We don't want to reveal that the email is not in the database for security reasons
            messages.success(request, "A password reset link has been sent to your email address if it exists in our system.")
            return redirect('accounts:password_reset_done')
    
    return render(request, 'registration/password_reset_form.html')


def password_reset_done(request):
    """View to show after a password reset email has been sent"""
    return render(request, 'registration/password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """View to confirm the reset link and allow the user to set a new password"""
    try:
        # Decode the user id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            if request.method == "POST":
                # Get the new password
                new_password = request.POST.get("new_password", "")
                confirm_password = request.POST.get("confirm_password", "")
                
                # Validate the passwords
                if new_password == confirm_password:
                    # Set the new password
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, "Your password has been reset successfully. You can now log in with your new password.")
                    return redirect('accounts:login')
                else:
                    messages.error(request, "Passwords do not match.")
            
            return render(request, 'registration/password_reset_confirm.html', {'validlink': True})
        else:
            # Token is invalid or expired
            return render(request, 'registration/password_reset_confirm.html', {'validlink': False})
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # Invalid user id
        return render(request, 'registration/password_reset_confirm.html', {'validlink': False})


def password_reset_complete(request):
    """View to show after a password has been successfully reset"""
    return render(request, 'registration/password_reset_complete.html')
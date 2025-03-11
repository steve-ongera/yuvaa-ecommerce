from django.urls import path
from .views import signup , activate , logout_view , view_profile, update_profile , login_view
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'


urlpatterns = [
    path("login/", login_view, name="login"),
    path('signup',signup , name='signup'),
    path('<str:username>/activate',activate),
    path('accounts/logout/', logout_view, name='logout'),

    path('profile/', view_profile, name='view_profile'),
    path('profile/update/', update_profile, name='update_profile'),

    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
]

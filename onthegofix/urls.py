"""
URL configuration for onthegofix project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing-page'),
    path('signup/', views.SignUpView.as_view(),name="signup"),
    path('veriify/email/', views.VerifyEmailView.as_view(),name="verify-email"),
    path('customer/index/', views.CustomerIndexView.as_view(),name="customer-index"),
    path('customer/index/detail/<int:pk>/', views.CustomerIndexDetailView.as_view(),name="customer-index-detail"),


    path('provider/index/', views.ProviderIndexView.as_view(),name="provider-index"),
    path('logout/',views.LogoutView.as_view(),name='signout'),
    path("get-location/<int:request_id>/", views.ProviderIndexView.as_view(), name="get_location"),
    path('signin/', views.SignInView.as_view(),name="signin"),
    path('provider/profile/update/', views.ServiceProviderProfileEditView.as_view(),name="provider-edit"),
    
    path('provider/profile/', views.ProviderProfileView.as_view(),name="provider-profile"),
    path('create/breakdown/request/<int:service_provider_id>/',views.BreakdownRequestCreateView.as_view(), name='create-breakdownrequest'),
    path('breakdown/details/<int:pk>/provider/',views.ProviderBreakdownRequestDetailView.as_view(), name='breakdownrequestprovider-detail'),
    path('breakdown/details/<int:pk>/customer/',views.CustomerBreakdownRequestDetailView.as_view(), name='breakdownrequestcustomer-detail'),
    path('customer/profile/update/',views.CustomerProfileEditView.as_view(), name='customer-edit'),
    path('customer/profile/',views.CustomerProfileListView.as_view(), name='customer-profile'),
    path('breakdown/request/update/<int:pk>/',views.BreakdownRequestUpdateView.as_view(), name='breakdownrequest-edit'),
    path('provider/dashboard/',views.ServiceProviderDashboardView.as_view(), name='provider-dashboard'),
    path('set/payment/<int:pk>',views.SetPaymentAmountView.as_view(), name='set-payment'),
    path('customer/dashboard/',views.CustomerDashboardView.as_view(), name='customer-dashboard'),
    path('customer/pay/<int:pk>/',views.CustomerPaymentView.as_view(), name='customer-payment'),
    path('razorpay/verify/', views.PaymentVerificationView.as_view(), name='razorpay-verification'),
    path('provider/history/',views.ServiceProviderHistoryView.as_view(), name='provider-history'),
    path('customer/history/',views.CustomerHistoryView.as_view(), name='customer-history'),
    path('rating/create/<int:pk>/', views.CreateRatingView.as_view(), name='create-rating'),
    path('ratings/<int:pk>/', views.RatingListView.as_view(), name='rating_list'),
    path('password/reset/', views.PasswordResestView.as_view(), name='password-reset'),
]
if settings.DEBUG:  # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

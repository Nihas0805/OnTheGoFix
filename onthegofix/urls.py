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
    path('signup/', views.SignUpView.as_view(),name="signup"),
    path('veriify/email/', views.VerifyEmailView.as_view(),name="verify-email"),
    path('customer/index/', views.CustomerIndexView.as_view(),name="customer-index"),
    path('provider/index/', views.ProviderIndexView.as_view(),name="provider-index"),
    path("get-location/<int:request_id>/", views.ProviderIndexView.as_view(), name="get_location"),
    path('signin/', views.SignInView.as_view(),name="signin"),
    path('provider/profile/update/', views.ServiceProviderProfileEditView.as_view(),name="provider-edit"),
    
    path('provider/profile/', views.ProviderProfileView.as_view(),name="provider-profile"),
    path('create/breakdown/request/<int:service_provider_id>/',views.BreakdownRequestCreateView.as_view(), name='create-breakdownrequest'),
    path('customer/profile/update/',views.CustomerProfileEditView.as_view(), name='customer-edit'),
    path('customer/profile/',views.CustomerProfileListView.as_view(), name='customer-profile'),
    path('breakdown/request/update/<int:pk>/',views.BreakdownRequestUpdateView.as_view(), name='breakdownrequest-edit'),
    path('provider/dashboard/view/',views.ServiceProviderDashboardView.as_view(), name='provider-dashboard'),
    path('set/payment/<int:pk>',views.SetPaymentAmountView.as_view(), name='set-payment'),
]
if settings.DEBUG:  # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import include, path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from .views import SignUpView
from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    # path("accounts/", include("django.contrib.auth.urls")),
    path('', TemplateView.as_view(template_name="home.html"), name="home"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path('add_stock/', views.StockController().add_stock, name='add_stock'),
    path('farm_detail/<str:symbol>/', views.StockController().stock_detail, name='stock_detail'),
    path('delete_farm/<str:symbol>/', views.StockController().delete_stock, name='delete_stock'),
    path('update_farm/<str:symbol>/<str:name>/<str:date>/', views.StockController().update_stock, name='update_stock'),
    path('delete_field/<str:symbol>/', views.StockController().delete_stock, name='delete_stock'),
    path('update_field/', views.StockController().update_stock_list, name='update_stock_list'),
    path('report_list/', views.StockController().stock_list, name='stock_list'),
    path('update_report/', views.StockController().update_stock_list, name='update_stock_list'),
    path('delete_field/', views.StockController().update_stock_list, name='update_stock_list'),
    path('analysis_list/', views.StockController().stock_list, name='stock_list'),
]

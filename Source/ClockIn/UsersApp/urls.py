from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # --- Regular subpages
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Admin subpages
    path('admin/', views.admin_view),
    path('admin/addUser', views.admin_add_user, name="add_user"),
    path('admin/manageUsers', views.admin_manage_users, name="manage_users")
]

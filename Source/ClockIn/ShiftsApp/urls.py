from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # --- Regular subpages
    path('shiftsView/', views.shifts_view, name="shifts_view"),
    path('manageShiftsView/', views.manage_shifts_view, name="manageShiftsView"),
    path('startShift/', views.start_shift, name="start_shift"),
    path('endShift/', views.end_shift, name="end_shift"),
    path('calculateSalary/', views.calculate_salary, name="calculate_salary"),

    # --- Admin subpages
    path('admin/manageSchedule/', views.manage_schedule, name="manage_schedule"),
    path('admin/usersSalary/', views.get_user_salary, name="get_user_salary"),
    path('admin/manageShifts/', views.admin_manage_shifts, name="manage_shifts")
]
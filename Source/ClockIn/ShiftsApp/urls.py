from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('shiftsView/', views.shifts_view, name="shifts_view"),
    path('manageShiftsView/', views.manage_shifts_view, name="manageShiftsView"),
    path('startShift/', views.start_shift, name="start_shift"),
    path('endShift/', views.end_shift, name="end_shift")
]
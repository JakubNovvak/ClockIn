from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('shiftsView/', views.shifts_view, name="shifts_view"),
    path('manageShiftsView/', views.manage_shifts_view),
]
from django.db import models
from UsersApp.models import User

class ShiftType(models.Model):
    shift_type_name = models.CharField(max_length=100)

class HourlyShift(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    work_date = models.DateField()

class CalendarShift(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE)

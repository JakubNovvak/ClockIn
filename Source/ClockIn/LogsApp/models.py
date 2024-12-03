from django.db import models
from UsersApp.models import User
from ShiftsApp.models import CalendarShift

class ShiftLog(models.Model):
    calendar_shift = models.ForeignKey(CalendarShift, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=50)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

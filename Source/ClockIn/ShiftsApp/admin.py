from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ShiftType)
admin.site.register(HourlyShift)
admin.site.register(CalendarShift)
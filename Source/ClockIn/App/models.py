from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=100)

class Department(models.Model):
    department_name = models.CharField(max_length=100)

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

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

class ShiftLog(models.Model):
    calendar_shift = models.ForeignKey(CalendarShift, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=50)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

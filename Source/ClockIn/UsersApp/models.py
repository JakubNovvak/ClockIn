from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    role_name = models.CharField(max_length=100)

class Department(models.Model):
    department_name = models.CharField(max_length=100)

# class User(models.Model):
#     username = models.CharField(max_length=100)
#     password = models.CharField(max_length=100, null=True)
#     email = models.EmailField(max_length=100)
#     role = models.ForeignKey(Role, on_delete=models.CASCADE)
#     department = models.ForeignKey(Department, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    hourly_rate = models.FloatField(null=True, blank=False)
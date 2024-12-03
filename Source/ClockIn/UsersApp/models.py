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

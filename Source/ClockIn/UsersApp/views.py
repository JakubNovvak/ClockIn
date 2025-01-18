from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login , logout
from django.contrib import messages
from UsersApp.models import User
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
def admin_required(user):
    return user.is_authenticated and user.is_superuser
def user_required(user):
    return not user.is_superuser

def login_view(request):
    context = {
        "errorMessage": ""
    }

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            print("Zalogowano")
            if user.username == "admin":
                return redirect('/users/admin')
            else:
                return redirect('/')  # Przekierowanie na stronę główną po zalogowaniu
        else:
            print("Błąd logowania")
            context["errorMessage"] = "Nieprawidłowa nazwa użytkownika lub hasło."
            messages.error(request, "Nieprawidłowa nazwa użytkownika lub hasło.")
            
    return render(request, 'loginView.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url="/users/login")
@user_passes_test(admin_required, login_url='/')
def admin_view(request):
    context = {
        'username': request.user.username,
    }
    return render(request, 'adminHomeView.html', context)


@login_required(login_url="/users/addUser")
@user_passes_test(admin_required, login_url='/')
def admin_add_user(request):
    context = {
        'responseMessage': None,
        'requestState': True
    }

    # TODO: logika dodawania użytkownika

    if request.method == "POST":

        # TODO: Hashowanie hasła w bazie danych
        new_user = User(
            username = request.POST.get("username"), 
            first_name = request.POST.get("name"),
            last_name = request.POST.get("surname"), 
            email = request.POST.get("email"),
            password = request.POST.get("password"),
            hourly_rate = request.POST.get("hourlyRate"),
        )

        new_user.save()
        
        context['responseMessage'] = f"Pomyślnie dodano użytkownika {request.POST.get("name")} {request.POST.get("surname")}."

    return render(request, 'adminAddUser.html', context)


@login_required(login_url="/users/manageUsers")
@user_passes_test(admin_required, login_url='/')
def admin_manage_users(request):
    context = {
        
    }

    # TODO: logika zarządzania użytkownikami

    return render(request, 'adminManageUsers.html', context)



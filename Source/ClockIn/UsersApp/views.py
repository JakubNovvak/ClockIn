from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login , logout
from django.contrib import messages
from UsersApp.models import User, Department
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password

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

    if request.method == "POST":

        # TODO: Hashowanie hasła w bazie danych
        new_user = User(
            username = request.POST.get("username"), 
            first_name = request.POST.get("name"),
            last_name = request.POST.get("surname"), 
            email = request.POST.get("email"),
            password = make_password(request.POST.get("password")), # Hashowanie hasła
            hourly_rate = request.POST.get("hourlyRate"),
        )

        new_user.save()
        
        context['responseMessage'] = f"Pomyślnie dodano użytkownika {request.POST.get("name")} {request.POST.get("surname")}."

    return render(request, 'adminAddUser.html', context)


@login_required(login_url="/users/manageUsers")
@user_passes_test(admin_required, login_url='/')
def admin_manage_users(request):
    context = {
        'users': [],
        'departments': []
    }

    if request.method == "POST":
        user_to_update = get_object_or_404(User, id=request.POST.get("user_id"))

        user_to_update.first_name = request.POST.get("name")
        user_to_update.last_name = request.POST.get("surname")
        user_to_update.username = request.POST.get("username")
        user_to_update.email = request.POST.get("email")
        user_to_update.department_id = request.POST.get("department_id")
        user_to_update.hourly_rate = float(request.POST.get("hourlyRate"))

        user_to_update.is_active = bool(request.POST.get("is_active"))

        user_to_update.save()

        print('Aktualizacja Usera')

    context['users'] = User.objects.filter(is_superuser=False)
    context['departments'] = Department.objects.all()

    for user in context['users']:
        if user.hourly_rate == None:
            user.hourly_rate = 0.1
        else:
            user.hourly_rate = float(user.hourly_rate)
            print(user.hourly_rate)


    return render(request, 'adminManageUsers.html', context)



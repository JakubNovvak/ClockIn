from django.shortcuts import render

def home_view(request):
    aa = {
        'user_id': request.user.id,  # ID zalogowanego użytkownika
        'username': request.user.username,  # Nazwa użytkownika
    }
    return render(request, 'homeView.html', aa)
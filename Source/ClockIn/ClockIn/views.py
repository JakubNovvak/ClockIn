from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url="/users/login")
def home_view(request):
    aa = {
        'user_id': request.user.id,  # ID zalogowanego użytkownika
        'username': request.user.username,  # Nazwa użytkownika
    }
    return render(request, 'homeView.html', aa)
    # if request.user.id == None:
    #     return render(request, 'loginView.html')
    # else:
    #     return render(request, 'homeView.html', aa)
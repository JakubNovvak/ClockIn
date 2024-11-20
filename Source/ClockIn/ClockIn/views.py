from django.shortcuts import render

def widok_logowania(request):
    return render(request, 'loginView.html')

def widok_godzin(request):
    return render(request, 'shiftsView.html')

def widok_zmiany(request):
    return render(request, 'manageShiftView.html')

def widok_strony_glownej(request):
    return render(request, 'homeView.html')
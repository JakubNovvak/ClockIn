from django.shortcuts import render

def widok_strony_glownej(request):
    return render(request, 'homeView.html')
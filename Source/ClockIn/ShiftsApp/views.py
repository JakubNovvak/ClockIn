from django.shortcuts import render

# Create your views here.
def shifts_view(request):
    return render(request, 'shiftsView.html')

def manage_shifts_view(request):
    return render(request, 'manageShiftView.html')
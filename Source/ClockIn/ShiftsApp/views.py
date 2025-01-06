from django.shortcuts import render, redirect
from django.utils.timezone import localtime
from datetime import timedelta
from .models import HourlyShift
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url="/users/login")
def shifts_view(request):
    context = {
        "shifts": [],
        "total_hours": 0,
        "total_minutes": 0,
        "error_message": "",
        "selected_date": ""
    }
    
    if request.method == "POST":
        selected_date = request.POST.get("selected_date")
        context["selected_date"] = request.POST.get("selected_date")
        if not selected_date:
            context["error_message"] = "Proszę wybrać datę."
            return render(request, "shiftsView.html", context)
        
        # Pobranie zmian użytkownika dla danej daty
        user_shifts = HourlyShift.objects.filter(
            user=request.user,
            work_date=selected_date
        ).order_by("start_time")
        
        if not user_shifts.exists():
            context["error_message"] = "Brak zmian w wybranej dacie."
        else:
            total_minutes = 0
            shifts_data = []
            for shift in user_shifts:
                print(shift.work_date)
                start_time = localtime(shift.start_time)
                end_time = localtime(shift.end_time) if shift.end_time else None
                
                if end_time:
                    # Wyliczenie czasu pracy
                    duration = end_time - start_time
                    total_minutes += duration.total_seconds() // 60
                
                shifts_data.append({
                    "start_time": start_time.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M") if end_time else "teraz",
                })

            context["shifts"] = shifts_data
            context["total_hours"] = int(total_minutes // 60)
            context["total_minutes"] = int(total_minutes % 60)
    
    return render(request, "shiftsView.html", context)

# def shifts_view(request):
#     return render(request, 'shiftsView.html')
@login_required(login_url="/users/login")
def manage_shifts_view(request):
    context = {
        "ongoingShift" : None
    }
    ongoingShift = filterOngoingShiftToday(request.user)
    context["ongoingShift"] = ongoingShift

    return render(request, 'manageShiftView.html', context)

@login_required(login_url="/users/login")
def start_shift(request):
    start_date = localtime()
    new_shift = HourlyShift(user = request.user,start_time=start_date,work_date=start_date)
    new_shift.save()
    return redirect('manageShiftsView')

@login_required(login_url="/users/login")
def end_shift(request):
    end_date = localtime()
    shift_to_update = filterOngoingShiftToday(request.user)
    shift_to_update.end_time = end_date
    shift_to_update.save()
    return redirect('manageShiftsView')

def filterOngoingShiftToday(_user):
    ongoingShift = HourlyShift.objects.filter(
        user=_user,
        end_time = None,
        work_date = localtime().date()
    ).first()
    return ongoingShift
        


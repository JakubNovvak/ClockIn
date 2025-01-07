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
        user_shifts = getUserShiftsOfTheDay(request.user, selected_date)
        if not user_shifts.exists():
            context["error_message"] = "Brak zmian w wybranej dacie."
        else:
            total_minutes = 0
            shifts_data = []
            
            for shift in user_shifts:
                # Wyliczenie czasu pracy
                if shift.end_time:
                    duration = shift.end_time - shift.start_time
                    total_minutes += duration.total_seconds() // 60
                convertTimeFormatToHH_MM(shift)
                shifts_data.append({
                    "start_time": shift.start_time,
                    "end_time": shift.end_time
                })

            context["shifts"] = shifts_data
            context["total_hours"] = int(total_minutes // 60)
            context["total_minutes"] = int(total_minutes % 60)
    
    return render(request, "shiftsView.html", context)

# def shifts_view(request):
#     return render(request, 'shiftsView.html')
@login_required(login_url="/users/login") # Jak zrobić zmiany nocne?
def manage_shifts_view(request):
    context = {
        "ongoingShift" : None,
        "errorMessage" : None,
        "shifts" : None,
        "total_hours": None,
        "totam_minutes": None
    }
    inclompleteShift = filterOngoingShiftsBeforeToday(request.user)
    if(inclompleteShift):
        errorMessage = "Masz zmiany, które nie zostały prawidłowo zakończone. Skontaktuj się z Administratorem."
        context["errorMessage"] = errorMessage
    ongoingShift = filterOngoingShiftToday(request.user)
    if(ongoingShift):
        # start_time = localtime(ongoingShift.start_time)
        # end_time = localtime(ongoingShift.end_time) if ongoingShift.end_time else None
        # ongoingShift.start_time = start_time.strftime("%H:%M")
        # ongoingShift.end_time = end_time.strftime("%H:%M") if end_time else "teraz"
        convertTimeFormatToHH_MM(ongoingShift)
    
    context["ongoingShift"] = ongoingShift

    today = localtime().date()
    shifts = getUserShiftsOfTheDay(request.user, today)
    # shifts_data = convertTimeFormatToHH_MM(shifts)
    shifts_data = []
    total_minutes = 0
    for shift in shifts:
        if shift.end_time:
            duration = shift.end_time - shift.start_time
            total_minutes += duration.total_seconds() // 60
        convertTimeFormatToHH_MM(shift)
        shifts_data.append({
            "start_time": shift.start_time,
            "end_time": shift.end_time
        })
    context["shifts"] = shifts_data
    context["total_hours"] = int(total_minutes // 60)
    context["total_minutes"] = int(total_minutes % 60)
    return render(request, 'manageShiftView.html', context)

@login_required(login_url="/users/login")
def start_shift(request):
    start_date = localtime()
    new_shift = HourlyShift(user = request.user,start_time=start_date,work_date=start_date.date())
    new_shift.save()
    return redirect('manageShiftsView')

@login_required(login_url="/users/login")
def end_shift(request):
    end_date = localtime()
    shift_to_update = filterOngoingShiftToday(request.user)
    shift_to_update.end_time = end_date
    shift_to_update.save()
    return redirect('manageShiftsView')


# ---------------------FUNKCJE POMOCNICZE---------------------
def filterOngoingShiftToday(_user):
    ongoingShift = HourlyShift.objects.filter(
        user=_user,
        end_time = None,
        work_date = localtime().date()
    ).first()
    return ongoingShift

def filterOngoingShiftsBeforeToday(_user):
    ongoingShift = HourlyShift.objects.filter(
        user=_user,
        end_time = None,
        work_date__lt = localtime().date()
    )
    return ongoingShift
        
def getUserShiftsOfTheDay(_user, _date):
    shifts_of_the_day = HourlyShift.objects.filter(
        user = _user,
        work_date = _date
    ).order_by("start_time")
    return shifts_of_the_day

# def convertTimeFormatToHH_MM(shifts):
#     converted_shifts = []
#     for shift in shifts:
#         start_time = localtime(shift.start_time)
#         end_time = localtime(shift.end_time) if shift.end_time else None
#         converted_shifts.append({
#             "start_time": start_time.strftime("%H:%M"),
#             "end_time": end_time.strftime("%H:%M") if end_time else "teraz"
#         })
#     return converted_shifts

def convertTimeFormatToHH_MM(shift):
    start_time = localtime(shift.start_time)
    end_time = localtime(shift.end_time) if shift.end_time else None
    shift.start_time = start_time.strftime("%H:%M")
    shift.end_time = end_time.strftime("%H:%M") if end_time else "teraz"
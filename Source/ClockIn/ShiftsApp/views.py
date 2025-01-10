from django.shortcuts import render, redirect
from django.utils.timezone import localtime
from datetime import date
import calendar
from .models import HourlyShift
from .models import CalendarShift
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


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
        "ongoingShift": None,
        "errorMessage": None,
        "shifts": None,
        "total_hours": None,
        "total_minutes": None,
        "days_in_month": [],  # Nowa zmienna na dni w miesiącu
        "work_hours_per_day": {},  # Dodatkowa zmienna na godziny pracy w każdym dniu
    }

    # Sprawdzanie nieukończonych zmian
    incompleteShift = filterOngoingShiftsBeforeToday(request.user)
    if incompleteShift:
        errorMessage = "Masz zmiany, które nie zostały prawidłowo zakończone. Skontaktuj się z Administratorem."
        context["errorMessage"] = errorMessage

    # Sprawdzanie trwającej zmiany
    ongoingShift = filterOngoingShiftToday(request.user)
    if ongoingShift:
        convertTimeFormatToHH_MM(ongoingShift)

    context["ongoingShift"] = ongoingShift

    today = localtime().date()
    shifts = getUserShiftsOfTheDay(request.user, today)
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

   # Generowanie dni w bieżącym miesiącu
    current_year = today.year
    current_month = today.month
    days_in_month = []
    work_hours_per_day = {}

    _, num_days = calendar.monthrange(current_year, current_month)
    
    for day in range(1, num_days + 1):
        day_str = f"{current_year}-{current_month:02d}-{day:02d}"
        total_minutes_day = 0
        shifts_of_day = getUserShiftsOfTheDay(request.user, day_str)

        for shift in shifts_of_day:
            if shift.end_time:
                duration = shift.end_time - shift.start_time
                total_minutes_day += duration.total_seconds() // 60

        hours = int(total_minutes_day // 60)
        minutes = int(total_minutes_day % 60)

        tmp = get_calendar_shifts(request.user, current_year, current_month)
        # for x in tmp:
        #     print(tmp)
        
        for shift in tmp:
            if shift['date'] == day_str:  
                days_in_month.append({
                    "day": day,
                    "date": day_str,
                    "hours": hours,
                    "minutes": minutes,
                    "startTime": shift['startTime'],  
                })
                print(shift)
                break


    context["days_in_month"] = days_in_month

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

@login_required(login_url="/users/login")
def calculate_salary(request):
    context = {
        "total_hours": None,
        "total_minutes": None,
        "total_salary": None,
        "error": None
    }

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        hourly_rate = request.POST.get("hourly_rate")

        if not start_date or not end_date or not hourly_rate:
            context["error"] = "Wszystkie pola (daty i stawka godzinowa) są wymagane."
            return render(request, "calculateSalary.html", context)

        try:
            hourly_rate = float(hourly_rate)
        except ValueError:
            context["error"] = "Stawka godzinowa musi być liczbą."
            return render(request, "calculateSalary.html", context)

        if start_date > end_date:
            context["error"] = "Data początkowa nie może być późniejsza niż data końcowa."
            return render(request, "calculateSalary.html", context)

        shifts = HourlyShift.objects.filter(
            user=request.user,
            work_date__range=(start_date, end_date)
        )

        total_minutes = 0
        for shift in shifts:
            if shift.end_time:
                duration = shift.end_time - shift.start_time
                total_minutes += duration.total_seconds() // 60

        # Obliczenia
        total_hours = total_minutes / 60
        total_salary = total_hours * hourly_rate

        context["total_hours"] = int(total_hours)
        context["total_minutes"] = int(total_minutes % 60)
        context["total_salary"] = round(total_salary, 2)

    return render(request, "calculateSalary.html", context)


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
    
    
    
    
    
    
    
    
    
    
    
    
def get_calendar_shifts(user, year, month):
    _, num_days = calendar.monthrange(year, month)
    days_in_month = []

    for day in range(1, num_days + 1):
        day_date = date(year, month, day)
        shift = CalendarShift.objects.filter(shift_date=day_date, user=user).first()

        if shift:
            days_in_month.append({
                "date": shift.shift_date,
                "startTime": shift.start_time,
                "endTime": shift.end_time,
                "shift_type": shift.shift_type
            })
        else:
            # Możesz dodać domyślne wartości lub pominąć ten dzień
            days_in_month.append({
                "date": day_date,
                "startTime": None,
                "endTime": None,
                "shift_type": None
            })

    return days_in_month


# @login_required(login_url="/users/login")
# def get_shift_details(request, date):
#     shifts = CalendarShift.objects.filter(shift_date=date)
#     shifts_data = [
#         {
#             "start_time": shift.start_time,
#             "end_time": shift.end_time,
#             "shift_type": shift.shift_type.name,
#             "shift_color": shift.shift_type.color_code,
#             "employee_id": shift.employee_id,
#         }
#         for shift in shifts
#     ]

#     return JsonResponse({"shifts": shifts_data})
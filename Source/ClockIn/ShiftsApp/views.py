from django.shortcuts import render, redirect
from django.utils.timezone import localtime
from datetime import timedelta, datetime
from UsersApp.views import user_required, admin_required
from .models import HourlyShift, CalendarShift, ShiftType
from UsersApp.models import User
from calendar import monthrange
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
@login_required(login_url="/users/login")
@user_passes_test(user_required, login_url='/users/admin')
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
@user_passes_test(user_required, login_url='/users/admin')
def manage_shifts_view(request):
    context = {
        "ongoingShift": None,
        "errorMessage": None,
        "shifts": None,
        "total_hours": None,
        "total_minutes": None,
        "month_name": None,
        "year": None,
        "weeks": None,
    }

    # Sprawdzenie niezakończonych zmian
    incompleteShift = filterOngoingShiftsBeforeToday(request.user)
    if incompleteShift:
        errorMessage = "Masz zmiany, które nie zostały prawidłowo zakończone. Skontaktuj się z Administratorem."
        context["errorMessage"] = errorMessage

    # Sprawdzenie bieżącej zmiany
    ongoingShift = filterOngoingShiftToday(request.user)
    if ongoingShift:
        convertTimeFormatToHH_MM(ongoingShift)
    
    context["ongoingShift"] = ongoingShift

    # Pobierz dane dotyczące zmian na dzisiaj
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

    # Generowanie kalendarza
    month = today.month
    year = today.year

    # Pobierz dane dotyczące zmian dla wybranego miesiąca
    calendar_shifts = CalendarShift.objects.filter(
        user=request.user,
        shift_date__month=month,
        shift_date__year=year
    )

    # Przygotuj dane kalendarza
    num_days_in_month = monthrange(year, month)[1]  # Liczba dni w miesiącu
    first_day_of_week = monthrange(year, month)[0]  # Dzień tygodnia, w którym zaczyna się miesiąc
    days = []


    # Dodaj puste dni na początku miesiąca, jeśli miesiąc zaczyna się od np. środy
    for _ in range(first_day_of_week):
        days.append(None)

    # Dodaj dni miesiąca
    for day in range(1, num_days_in_month + 1):
        day_shifts = calendar_shifts.filter(shift_date__day=day)
        days.append({
            'day': day,
            'shifts': day_shifts,
        })

    # Podziel dni na tygodnie (7 dni na tydzień)
    weeks = [days[i:i+7] for i in range(0, len(days), 7)]

    # Przygotuj dane dla shift_data
    context["shifts_data"] = [
        {
            "day": day['day'],
            "shifts": [
                {
                    "shift_type": shift.shift_type.shift_type_name,
                    "start_time": shift.start_time,
                    "end_time": shift.end_time,
                }
                for shift in day['shifts'] 
            ]
        }
        for week in weeks
        for day in week
        if day and day['shifts']
    ]

    # Dodaj dane kalendarza do kontekstu
    context["month_name"] = today.strftime("%B")
    context["year"] = year
    context["weeks"] = weeks

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
@user_passes_test(user_required, login_url='/users/admin')
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

@login_required(login_url="/users/login")
@user_passes_test(admin_required, login_url='/')
def manage_schedule(request):
    context = {
        "users": [],
        "shift_types": ShiftType.objects.all(),
        "errorMessage": None
    }
    users = User.objects.filter(
        is_superuser = 0  
    )
    context["users"] = users
    
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        shift_type_id = request.POST.get("shift_type_id")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        
        if start_date > end_date:
            context["errorMessage"] = "Data początkowa nie może być późniejsza niż końcowa."
            return render(request, "manageScheduleView.html", context)
        if end_time < start_time:
            context["errorMessage"] = "Godzina rozpoczęcia nie może być późniejsza niż godzina zakończenia."
            return render(request, "manageScheduleView.html", context)
        
        if user_id and start_date and end_date and shift_type_id and start_time and end_time:
            user = User.objects.get(id=user_id)
            shift_type = ShiftType.objects.get(id=shift_type_id)
            
            overlapping_shifts = CalendarShift.objects.filter(
                user=user,
                shift_date__range=(start_date, end_date)
            )
            if overlapping_shifts.exists():
                context["errorMessage"] = "Istnieją już zmiany w wybranym zakresie dat dla tego użytkownika"
                return render(request, "manageScheduleView.html", context)
            
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            current_date = start_date_obj
            while current_date <= end_date_obj:
                CalendarShift.objects.create(
                    user=user,
                    shift_date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    shift_type=shift_type
                )
                current_date += timedelta(days=1)
        else:
            context["errorMessage"] = "Wszystkie pola są wymagane"
        
    return render(request, "manageScheduleView.html", context)

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

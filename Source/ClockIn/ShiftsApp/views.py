from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta, datetime
from UsersApp.views import user_required, admin_required
from .models import HourlyShift, CalendarShift, ShiftType
from UsersApp.models import User, Department
from UsersApp.views import user_required
from calendar import monthrange
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from reportlab.lib.colors import black


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
        errorMessage = "Masz zmiany, które nie zostaly prawidlowo zakończone. Skontaktuj się z Administratorem."
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
        hourly_rate = request.user.hourly_rate
        action = request.POST.get("action")

        print(hourly_rate)
        
        if not start_date or not end_date:
            context["error"] = "Wszystkie pola są wymagane."
            return render(request, "calculateSalary.html", context)

        if start_date > end_date:
            context["error"] = "Data początkowa nie może być późniejsza niż data końcowa."
            return render(request, "calculateSalary.html", context)

        shifts = HourlyShift.objects.filter(
            user=request.user,
            work_date__range=(start_date, end_date)
        )

        total_minutes = 0
        total_salary = 0
        shift_details = []

        for shift in shifts:
            if shift.end_time:
                duration = shift.end_time - shift.start_time
                shift_minutes = duration.total_seconds() // 60
                shift_hours = shift_minutes / 60
                shift_salary = shift_hours * hourly_rate

                total_minutes += shift_minutes
                total_salary += shift_salary

                convertTimeFormatToHH_MM(shift)

                shift_details.append({
                    "work_date": shift.work_date,
                    "start_time": shift.start_time,
                    "end_time": shift.end_time,
                    "hours": int(shift_hours),
                    "minutes": int(shift_minutes % 60),
                    "salary": round(shift_salary, 2)
                })

        total_hours = total_minutes / 60
        context["total_hours"] = int(total_hours)
        context["total_minutes"] = int(total_minutes % 60)
        context["total_salary"] = round(total_salary, 2)
        context["shift_details"] = shift_details

        # Generowanie raportu PDF
        if action == "download":
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)

            # Naglówek
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 750, "Raport wynagrodzenia")
            p.setFont("Helvetica", 12)
            p.drawString(100, 730, f"Uzytkownik: {request.user.first_name} {request.user.last_name}")
            p.drawString(100, 710, f"Okres od: {start_date} do: {end_date}")
            p.drawString(100, 690, f"Przepracowane godziny: {int(total_hours)} godz. {int(total_minutes % 60)} min.")
            p.drawString(100, 670, f"Stawka godzinowa: {hourly_rate} zl")
            p.drawString(100, 650, f"Laczne wynagrodzenie: {round(total_salary, 2)} zl")

            # Linie oddzielające sekcje
            p.setStrokeColor(black)
            p.setLineWidth(1)
            p.line(50, 640, 550, 640)

            # Szczególy zmian
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 620, "Szczegoly zmian:")
            p.setFont("Helvetica", 10)

            y_position = 600
            for shift in shift_details:
                p.drawString(100, y_position, f"{shift['work_date']} {shift['start_time']} - {shift['end_time']}: "
                                             f"{shift['hours']} godz. {shift['minutes']} min. - {shift['salary']} zl")
                y_position -= 15

            # Zakończenie strony
            p.showPage()
            p.save()
            buffer.seek(0)

            # Zwrócenie pliku PDF jako odpowiedź
            return FileResponse(buffer, as_attachment=True, filename="raport_wynagrodzenia.pdf")

    return render(request, "calculateSalary.html", context)


@login_required(login_url="/users/login")
@user_passes_test(admin_required, login_url='/')
def get_user_salary(request):
    context = {
        "departments" : [],
        "users": [],
        "salary": None,
        "start_date": None,
        "end_date": None,
        "selected_user": None,
        "errorMessage": None
    }
    departments = Department.objects.all()
    context["departments"] = departments
    selected_department_id = request.GET.get("department_id")
    if selected_department_id:
        users = User.objects.filter(department_id=selected_department_id, is_superuser=False)
    else:
        users = User.objects.filter(is_superuser=False)
    context["users"] = users
    
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        
        if not user_id or not start_date or not end_date:
            context["errorMessage"] = "Proszę wybrać użytkownika oraz zakres dat."
            return render(request, "allUsersSalaryView.html", context)
        if start_date > end_date:
            context["errorMessage"] = "Data początkowa nie może być późniejsza niż końcowa."
            return render(request, "allUsersSalaryView.html", context)
        user = User.objects.get(id=user_id)
        
        shifts = HourlyShift.objects.filter(
            user=user,
            work_date__range = (start_date, end_date)
        )
        if not shifts.exists():
            context["errorMessage"] = "Brak zmian dla wybranego użytkownika i miesiąca."
            return render(request, "allUsersSalaryView.html", context)
            
        total_minutes = 0
        total_salary = 0
        hourly_rate = user.hourly_rate

        for shift in shifts:
            if shift.end_time:
                duration = shift.end_time - shift.start_time
                shift_minutes = duration.total_seconds() // 60
                shift_hours = shift_minutes / 60
                shift_salary = shift_hours * hourly_rate

                total_minutes += shift_minutes
                total_salary += shift_salary
                
        context["salary"] = round(total_salary, 2)
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["selected_user"] = user

    return render(request, "allUsersSalaryView.html", context)

# ------------------FUNKCJE ADMINISTRATORA ------------------------


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


@login_required(login_url="/users/login")
@user_passes_test(admin_required, login_url='/')
def admin_manage_shifts(request):
    context = {
        'users': [],
        'shifts': [],
        'selected_user_id': None
    }

    context['users'] = User.objects.all()

    
    if request.method == 'POST':
        shift_to_update = get_object_or_404(HourlyShift, id=request.POST.get("shift_id"))

        # Pobranie wartości z formularza
        work_date_str = request.POST.get("work_date")  # YYYY-MM-DD
        start_time_str = request.POST.get("start_time")  # HH:MM
        end_time_str = request.POST.get("end_time")  # HH:MM

        # Utworzenie obiektu daty
        work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()

        # Utworzenie obiektów czasu
        start_time = datetime.strptime(start_time_str, '%H:%M').timetz()
        end_time = datetime.strptime(end_time_str, '%H:%M').timetz()

        # Pełna timedate dla start_time
        start_datetime = datetime.combine(work_date, start_time)

        # Sprawdzenie, czy końcowa godzina jest późniejsza od start_time
        if end_time < start_time:
            # Dodaj dzień do daty end_time
            end_datetime = datetime.combine(work_date + timedelta(days=1), end_time)
        else:
            # Ten sam dzień dla end_time
            end_datetime = datetime.combine(work_date, end_time)

        # TODO: Zmienić tymczasowe rozwiązanie, z dodawaniem jednej godziny przy strefach czasowych
        start_datetime += timedelta(hours=1)
        end_datetime += timedelta(hours=1)

        # Aktualizacja rekordu
        shift_to_update.work_date = work_date  # Tylko data bez godziny
        shift_to_update.start_time = start_datetime  # Pełne datetime
        shift_to_update.end_time = end_datetime  # Pełne datetime

        print(shift_to_update.start_time)

        shift_to_update.save()

        context['selected_user_id'] = int(request.POST.get("selected_user_id"))
        context['shifts'] = HourlyShift.objects.filter(user=User.objects.get(id=request.POST.get("selected_user_id")))

    if request.GET.get('userId'):

        context["selected_user_id"] = int(request.GET.get('userId'))
        context['shifts'] = HourlyShift.objects.filter(user=User.objects.get(id=request.GET.get('userId')))


    for shift in context['shifts']:
        shift.work_date = shift.work_date.strftime('%Y-%m-%d')
        shift.start_time = shift.start_time.strftime('%H:%M')
        shift.end_time = shift.end_time.strftime('%H:%M') if shift.end_time != None else None

    return render(request, "adminManageShifts.html", context)


# ---------------------FUNKCJE POMOCNICZE--------------------------
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

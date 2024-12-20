from django.shortcuts import render, redirect, HttpResponse
from .models import *
from datetime import datetime, timedelta, date
from pyModbusTCP.client import ModbusClient
import threading
import time
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


c = ModbusClient(host="10.1.1.100", port=int(502), auto_open=True)
idel_cycle_time = None
ShiftTimeStart = None
last_break_count = 0
today = datetime.now()
Production_data = None
Scrap_data = None
flag_error = False
flag_hold = False

current_date = datetime.now().date()


def ModumDataFunc():
    global last_break_count, Production_data, Scrap_data, Run_time, Running_value, flag_error, flag_hold

    # Fetch all error definitions from the database
    error_labels = Errorlabels.objects.all()
    parameter_data = parameterlabel.objects.get()

    while True:
        Running_value = c.read_coils(int(parameter_data.runnig_bit))[0]
        Production_data = c.read_holding_registers(int(parameter_data.production_bit))[0]
        Scrap_data = c.read_holding_registers(int(parameter_data.scrap_bit))[0]
        Run_time = c.read_coils(int(parameter_data.runnig_bit))[0]

        # Initialize a flag to check for errors
        any_error = False

        # Read and evaluate error statuses
        for label in error_labels:
            error_name = label.ErrorName
            error_bit = label.ErrorBit
            error_status = c.read_discrete_inputs(int(error_bit))[0]

            # Adjust logic for "light_curtain" errors (reverse behavior)
            if error_name == "light_curtain":
                error_status = not error_status  # Reverse the status

            # If any error is true, set the `any_error` flag
            if error_status:
                any_error = True

            # Fetch the last saved alarm for the current error
            last_error_alarm = (
                ErrorDb.objects.filter(NameOfAlarm=error_name).order_by("-id").first()
            )
            last_error_value = (
                last_error_alarm.Alarm_value if last_error_alarm else None
            )

            # Log new error if detected
            if error_status and last_error_value != "True":
                error = ErrorDb(NameOfAlarm=error_name, Alarm_value="True")
                error.save()

            # Log resolved error if applicable
            if last_error_value == "True" and not error_status and Running_value:
                error = ErrorDb(NameOfAlarm=error_name, Alarm_value="False")
                error.save()

        # Evaluate flags based on Running_value and errors
        if Running_value:
            print("Running value is True - No errors")
            flag_hold = False
            flag_error = False
        elif any_error and not Running_value:
            print("Error detected and Running_value is False")
            flag_error = True
            flag_hold = True
        elif not any_error and not Running_value and not flag_hold:
            print("No errors and Running_value is False")
            flag_error = False

        time.sleep(1)


def ModumThreading():
    job_thread_E = threading.Thread(target=ModumDataFunc)
    job_thread_E.start()


def Alarmdatafunc():
    print("in alram data func")
    runtime_counter = 0
    global last_break_count, newpro
    last_break_count = 0
    all_breaks = PopupDataModel.objects.all()
    while True:
        current_time_obj = datetime.now().strftime("%H:%M")
        current_time_obj_1 = datetime.strptime(current_time_obj, "%H:%M").time()

        if Run_time == True:
            runtime_counter += 1

        break_data = None
        for break_data in all_breaks:
            break_start_time_str = break_data.BreakStartTime
            break_stop_time_str = break_data.BreakStopTime
            break_start_time = datetime.strptime(
                break_start_time_str, "%H:%M:%S"
            ).time()
            break_stop_time = datetime.strptime(break_stop_time_str, "%H:%M:%S").time()
            break_stop_time_minus_one_minute = (
                datetime.combine(datetime.today(), break_stop_time)
                - timedelta(minutes=1)
            ).time()

            if (
                break_start_time
                <= current_time_obj_1
                <= break_stop_time_minus_one_minute
            ):
                break
            else:
                break_data = None
        print("before if ")
        if break_data is not None:
            print("in if ")
            last_break_count += 1
            SaveToOeeDB = OEEData(
                Production=Production_data,
                Defective=Scrap_data,
                Planed_time=last_break_count - 1,  # Adjust planned time
                Runtime_is=runtime_counter,
            )
        else:
            print("in else")
            SaveToOeeDB = OEEData(
                Production=Production_data,
                Defective=Scrap_data,
                Planed_time=last_break_count,  # Use current planned time the
                Runtime_is=runtime_counter,
            )

        SaveToOeeDB.save()

        if Run_time == False:
            runtime_counter = runtime_counter

        if current_time_obj_1 == ShiftTimeStop_obj:
            newpro = Production_data
            break

        time.sleep(60)


def AlarmdatafuncThreading():
    job_thread_E1 = threading.Thread(target=Alarmdatafunc)
    job_thread_E1.start()


Final_performance = None
Final_Availabilty = None
Final_Quality = None
Final_OEE = None
capacity_is = None
production_is = None
last_production_values = None
last_datetime_values = None
last_defective_values = None
target = None
runtime = None
target_left = None
formatted_remaining_time = None
acceptedP = None
scrap_is = None
TotalAvailableShifttimeMinutes = None
total_break_duration = None
TotalShiftTimeinMinutes = None
Formattedtotal_break_durationMinutes = None
ShiftTimeStop = None


def HomePage(request):

    global final_availability_1, final_oee_1, final_performance_1, final_production_1, final_quality_1
    today = datetime.now()

    this_month = datetime.now().month
    variable1 = FinalOeeData.objects.filter(logged_on__month=this_month)
    production_list_1 = [data.production for data in variable1]
    performance_list_1 = [data.performance for data in variable1]
    availability_list_1 = [float(data.availability) for data in variable1]
    quality_list_1 = [float(data.quality) for data in variable1]
    oee_list_1 = [float(data.oee) for data in variable1]

    production_list_sum = sum(production_list_1)
    performance_list_sum = sum(performance_list_1)
    availability_list_sum = sum(availability_list_1)
    quality_list_sum = sum(quality_list_1)

    oee_list_sum = sum(oee_list_1)

    production_len = len(production_list_1)
    performance_len = len(performance_list_1)
    availability_len = len(availability_list_1)
    quality_len = len(quality_list_1)
    oee_len = len(oee_list_1)

    try:
        final_performance_1 = round(performance_list_sum / performance_len, 2)
    except ZeroDivisionError:
        final_performance_1 = 0
    try:
        final_production_1 = round(production_list_sum / production_len, 2)
    except ZeroDivisionError:
        final_production_1 = 0
    try:
        final_availability_1 = round(availability_list_sum / availability_len, 2)
    except ZeroDivisionError:
        final_availability_1 = 0
    try:
        final_quality_1 = round(quality_list_sum / quality_len, 2)
    except ZeroDivisionError:
        final_quality_1 = 0
    try:
        final_oee_1 = round(oee_list_sum / oee_len, 2)
    except ZeroDivisionError:
        final_oee_1 = 0

    data_for_last_five_days = []
    for day in range(4, -1, -1):
        date_for_day = today - timedelta(days=day)
        data_for_day = (
            OEEData.objects.filter(DateTime__date=date_for_day).order_by("-id").first()
        )
        data_for_last_five_days.append(data_for_day)
    production_graph = [
        data.Production if data else 0 for data in data_for_last_five_days
    ]
    scrap_graph = [data.Defective if data else 0 for data in data_for_last_five_days]
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month + timedelta(days=32)).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    month_data = FinalOeeData.objects.filter(
        logged_on__gte=start_of_month, logged_on__lt=end_of_month
    )
    performance_list = [data.performance for data in month_data]
    availability_list = [data.availability for data in month_data]
    quality_list = [data.quality for data in month_data]
    oee_list = [data.oee for data in month_data]
    context = {
        "Final_Quality": Final_Quality,
        "Final_performance": Final_performance,
        "Final_Availabilty": Final_Availabilty,
        "Final_OEE": Final_OEE,
        "capacity_is": capacity_is,
        "production_is": production_is,
        "production_graph": production_graph,
        "scrap_graph": scrap_graph,
        "last_production_values": last_production_values,
        "last_datetime_values": last_datetime_values,
        "last_defective_values": last_defective_values,
        "target": target,
        "final_availability_1": final_availability_1,
        "final_oee_1": final_oee_1,
        "final_performance_1": final_performance_1,
        "final_production_1": final_production_1,
        "final_quality_1": final_quality_1,
        "runtime": runtime,
        "target_left": target_left,
        "formatted_remaining_time": formatted_remaining_time,
        "acceptedP": acceptedP,
        "scrap_is": scrap_is,
    }
    return render(request, "home.html", context)


acceptedP1 = None

target = None

free_times = None
production_scrap_values = None

remaining_time = None


def home_page(request):
    # Get the current date

    today = datetime.now().date()

    # Get the last five rows from the database
    last_five_rows = OEEData.objects.order_by("-id")[:5]
    datefromdb = last_five_rows[4].DateTime.date()
    try:
        last_row = OEEData.objects.latest("id")
        row_date = last_row.DateTime.date()

        runtimeis = last_row.Runtime_is if row_date == current_date else 0
    except OEEData.DoesNotExist:
        # Handle the case when there are no records in the database
        runtimeis = 0

    last_five_rows1 = OEEData.objects.filter(DateTime__date=current_date).order_by(
        "-id"
    )[:15]

    # Initialize lists for free times and production-scrap values
    free_times = []
    production_scrap_values = []

    # Extract time and production - scrap value from the last five rows
    for row in reversed(last_five_rows1):
        free_times.append(row.DateTime.strftime("%H:%M"))
        production_scrap_values.append(int(row.Production) - int(row.Defective))

    # If there are less than 5 rows for today's date, fill remaining slots with zeros
    num_zeros_to_append = 15 - len(last_five_rows1)
    free_times += ["00:00"] * num_zeros_to_append
    production_scrap_values += [0] * num_zeros_to_append

    data_for_last_five_days = []
    for day in range(4, -1, -1):
        date_for_day = today - timedelta(days=day)
        data_for_day = (
            OEEData.objects.filter(DateTime__date=date_for_day).order_by("-id").first()
        )
        data_for_last_five_days.append(data_for_day)
    production_graph = [
        data.Production if data else 0 for data in data_for_last_five_days
    ]
    if data_for_last_five_days[4]:

        production_graph[4] = Production_data

    scrap_graph = [data.Defective if data else 0 for data in data_for_last_five_days]
    if data_for_last_five_days[4]:
        scrap_graph[4] = Scrap_data

    context = {
        "Final_Quality": Final_Quality if Final_Quality is not None else 0,
        "Final_performance": Final_performance if Final_performance is not None else 0,
        "Final_Availabilty": Final_Availabilty if Final_Availabilty is not None else 0,
        "Final_OEE": Final_OEE if Final_OEE is not None else 0,
        "capacity_is": capacity_is,
        "Runtime_is": runtimeis,
        "production_is": production_is,
        "ProductionGraphData": production_graph,  # Include ProductionGraphData key
        "ScrapGraphData": scrap_graph,
        "last_production_values": last_production_values,
        "last_datetime_values": last_datetime_values,
        "last_defective_values": last_defective_values,
        "target": target,
        "production_scrap_values": production_scrap_values,
        "free_times": free_times,
        "final_availability_1": final_availability_1,
        "final_oee_1": final_oee_1,
        "final_performance_1": final_performance_1,
        "final_production_1": final_production_1,
        "final_quality_1": final_quality_1,
        "runtime": runtime,
        "target_left": target_left,
        "formatted_remaining_time": formatted_remaining_time,
        "acceptedP": acceptedP,
        "scrap_is": scrap_is,
        "acceptedP1": acceptedP1,
        "remaining_time": (
            str(remaining_time) if remaining_time is not None else "00:00:00"
        ),
        "formatted_final_unplaned": formatted_final_unplaned,
    }

    return JsonResponse(context)


def DeatailPageload(request):

    global total_break_duration
    breakdatafromdb = PopupDataModel.objects.all()
    total_break_duration = timedelta()
    for break_data in breakdatafromdb:
        break_start_time = datetime.strptime(break_data.BreakStartTime, "%H:%M:%S")
        break_stop_time = datetime.strptime(break_data.BreakStopTime, "%H:%M:%S")
        break_duration = break_stop_time - break_start_time
        total_break_duration += break_duration
    context = {
        "breakdatafromdb": breakdatafromdb,
        "ShiftTimeStop": ShiftTimeStop,
    }
    return render(request, "details.html", context)


def popupData(request):
    if request.method == "POST":
        BreakName = request.POST.get("desc")
        Breakstart_str = request.POST.get("breakstart")
        Breakstop_str = request.POST.get("breakstop")
        Requested = request.POST.get("Requestemail")
        Approvel = request.POST.get("Approvedemail")
        Breakstart = datetime.strptime(Breakstart_str, "%H:%M").time()
        Breakstop = datetime.strptime(Breakstop_str, "%H:%M").time()
        savetodb = PopupDataModel(
            Descriptionis=BreakName,
            BreakStartTime=Breakstart,
            BreakStopTime=Breakstop,
            EmailRequested=Requested,
            Emailaproved=Approvel,
        )
        savetodb.save()
    return redirect(DeatailPageload)


def DeleteBreak(request, id):
    alldata = PopupDataModel.objects.get(id=id)
    alldata.delete()
    return redirect(DeatailPageload)


def Detailform(request):
    global idel_cycle_time
    global ShiftTimeStart, ShiftTimeStop
    global ShiftTimeStart_obj
    global ShiftTimeStop_obj
    global current_time_obj
    global target
    if request.method == "POST":
        ShiftTimeStart = request.POST.get("field1")
        ShiftTimeStop = request.POST.get("field2")
        idel_cycle_time = request.POST.get("field3")
        checking = request.POST.get("timeDifference")
        target = request.POST.get("field4")
        checking_time = datetime.strptime(checking, "%H:%M").strftime("%H:%M:%S")
        hours, minutes, seconds = map(int, checking_time.split(":"))
        total_minutes = (hours * 60) + minutes
        total_break_duration_td = timedelta(
            hours=total_break_duration.seconds // 3600,
            minutes=(total_break_duration.seconds // 60) % 60,
            seconds=total_break_duration.seconds % 60,
        )
        shift_timing_td = datetime.strptime(checking_time, "%H:%M:%S").time()
        result_td = (
            timedelta(
                hours=shift_timing_td.hour,
                minutes=shift_timing_td.minute,
                seconds=shift_timing_td.second,
            )
            - total_break_duration_td
        )
        result_str = str(result_td)
        current_time_obj = datetime.now().time()
        ShiftTimeStart_obj = datetime.strptime(ShiftTimeStart, "%H:%M").time()
        ShiftTimeStop_obj = datetime.strptime(ShiftTimeStop, "%H:%M").time()
        ModumThreading()
        tocallThreading()

        # AlarmdatafuncThreading()
        # dataThreading()
        # foractualval()
        breakdatafromdb = PopupDataModel.objects.all()
        context = {
            "result_str": result_str,
            "breakdatafromdb": breakdatafromdb,
            "ShiftTimeStop": ShiftTimeStop,
        }
    return render(request, "details.html", context)


def tocall():
    while True:
        current_time_obj = datetime.now().time()
        formatted_time = current_time_obj.strftime("%H:%M:%S")

        # Extract only hours and minutes, and add ":00" for seconds
        formatted_time_hours_minutes = formatted_time[:-3] + ":00"

        # Convert the formatted string back to datetime.time
        desired_time_obj = datetime.strptime(
            formatted_time_hours_minutes, "%H:%M:%S"
        ).time()

        if desired_time_obj == ShiftTimeStart_obj:

            AlarmdatafuncThreading()
            dataThreading()
            break

        time.sleep(1)


def tocallThreading():
    job_thread_E12 = threading.Thread(target=tocall)
    job_thread_E12.start()


FormattedTotalShiftTime = None
FormattedTotalAvailableShifttime = None
Formattedtotal_break_duration = None
formatted_final_unplaned = None
Formattedtotal_break_durationMinutes = None
Final_unplaned = None
Unplanned_Time_Percentage = None
TotalShiftTimeinMinutes = None
runtime = None
Available_Run_Time = None
FormattedTotalAvailableRunTime = None
Error_1_sum = None
Error_2_sum = None
Error_3_sum = None
Error_4_sum = None
Error_5_sum = None
Error_len_1 = None
Error_len_2 = None
Error_len_3 = None
Error_len_4 = None
Error_len_5 = None
unplaned_time = None


def to_read_data():
    global Error_statistics, Formattedtotal_break_duration, Formattedtotal_break_durationMinutes, Unplanned_Time_Percentage, Error_1_sum, remaining_time, unplaned_time
    global Error_2_sum, Error_3_sum, Error_4_sum, Error_5_sum, Error_len_1, Error_len_2, Error_len_3, Error_len_4, Error_len_5
    global acceptedP, scrap_is, Final_performance, Final_Quality, Final_Availabilty, Final_OEE, production_is, capacity_is, last_production_values, last_datetime_values, last_defective_values, formatted_final_unplaned, FormattedTotalShiftTime, FormattedTotalAvailableShifttime, TotalShiftTimeinMinutes, TotalAvailableShifttimeMinutes, Final_unplaned, runtime, FormattedTotalAvailableRunTime, Available_Run_Time, target_left
    break_duration_counter_seconds = 0  # Initialize the counter for seconds
    break_duration_counter_minutes = 0
    counter = -1
    previous_minute = datetime.now().time().minute
    instance_counter = 0

    while True:
        breakdatafromdb = PopupDataModel.objects.all()
        last_row = OEEData.objects.latest("id")

        production_is = int(last_row.Production)
        planned_time = int(last_row.Planed_time)
        scrap_is = int(last_row.Defective)
        acceptedP = production_is - scrap_is
        runtime = int(last_row.Runtime_is)
        current_datetime_objaa = datetime.now()
        current_minute = datetime.now().time().minute

        # Extract the current time rounded to the nearest minute
        current_time_rounded = current_datetime_objaa.replace(
            second=0, microsecond=0
        ).time()

        current_time_obj = datetime.now().time()
        formatted_time = current_time_obj.strftime("%H:%M")
        formatted_shift_time = ShiftTimeStop_obj.strftime("%H:%M")
        formatted_shift_time_obj = datetime.strptime(formatted_time, "%H:%M")
        formatted_time_obj = datetime.strptime(formatted_shift_time, "%H:%M")

        if formatted_shift_time_obj > formatted_time_obj:

            todayData = FinalOeeData(
                production=newpro,
                performance=Final_performance,
                availability=Final_Availabilty,
                quality=Final_Quality,
                oee=Final_OEE,
                defec=Scrap_data,
            )
            todayData.save()
            break
        remaining_time = formatted_time_obj - formatted_shift_time_obj

        formatted_time = current_time_obj.strftime("%H:%M:%S")

        # Extract only hours and minutes, and add ":00" for seconds
        formatted_time_hours_minutes = formatted_time[:-3] + ":00"

        # Convert the formatted string back to datetime.time
        desired_time_obj = datetime.strptime(
            formatted_time_hours_minutes, "%H:%M:%S"
        ).time()

        total_minutes = remaining_time.total_seconds() / 60
        hours, minutes = divmod(total_minutes, 60)
        formatted_remaining_time = f"{int(hours):02d}:{int(minutes):02d}"
        current_available_time_td = datetime.combine(
            datetime.today(), current_time_obj
        ) - datetime.combine(datetime.today(), ShiftTimeStart_obj)
        current_available_minutes = int(current_available_time_td.total_seconds() / 60)

        TotalShiftTime = datetime.combine(
            datetime.today(), ShiftTimeStop_obj
        ) - datetime.combine(datetime.today(), ShiftTimeStart_obj)
        FormattedTotalShiftTime = (
            (datetime.min + TotalShiftTime).time().strftime("%H:%M")
        )

        TotalShiftTimeinMinutes = int(TotalShiftTime.total_seconds() / 60)

        ide = last_row.pk
        if not breakdatafromdb:  # If no break data available
            unplaned_time = current_available_minutes - runtime
            Final_unplaned = unplaned_time
        else:
            instance_counter = 0

            for break_entry in breakdatafromdb:
                break_start_time = datetime.strptime(
                    break_entry.BreakStartTime, "%H:%M:%S"
                ).time()
                break_stop_time = datetime.strptime(
                    break_entry.BreakStopTime, "%H:%M:%S"
                ).time()

                if (
                    break_start_time < current_time_rounded <= break_stop_time
                    and Running_value == False
                ):
                    if current_minute != previous_minute:
                        counter += 1
                        previous_minute = current_minute
                        instance_counter += 1

                    # Decrease the counter when the second and third instances are encountered
                    if instance_counter == 2:
                        counter -= 1
                    elif instance_counter >= 3:
                        counter -= 1

                    # if break_duration_counter_minutes == 0:
                    #     break_duration_counter_minutes = 1

                    # break_duration_counter_seconds += 1

                    # # Check if 60 seconds have passed
                    # if break_duration_counter_seconds >= 60:
                    #     # If yes, increment the counter for minutes and reset the seconds counter
                    #     break_duration_counter_minutes += 1
                    #     break_duration_counter_seconds = 0
                    # break
                else:
                    unplaned_time = (
                        current_available_minutes
                        - runtime
                        - (0 if counter == -1 else counter)
                    )
                    Final_unplaned = unplaned_time

        # Now you have the total break duration in minutes

        formatted_final_unplaned = f"{Final_unplaned // 60:02}:{Final_unplaned % 60:02}"

        TotalAvailableShifttime = TotalShiftTime - total_break_duration
        FormattedTotalAvailableShifttime = (
            (datetime.min + TotalAvailableShifttime).time().strftime("%H:%M")
        )
        TotalAvailableShifttimeMinutes = int(
            TotalAvailableShifttime.total_seconds() / 60
        )
        Available_Run_Time = int(TotalAvailableShifttimeMinutes) - int(Final_unplaned)
        FormattedTotalAvailableRunTime = (
            f"{Available_Run_Time // 60:02}:{Available_Run_Time % 60:02}"
        )
        try:
            Performance_Production = int(idel_cycle_time) * int(production_is)
            Performance_Total_Minutes = current_available_minutes - (
                int(planned_time) + int(Final_unplaned)
            )
            Current_performance = (
                Performance_Production / Performance_Total_Minutes
            ) * 100
            Final_performance = round(Current_performance, 2)
        except ZeroDivisionError:
            Final_performance = 0
        try:
            Availabilty_Minutes = current_available_minutes - int(
                planned_time + Final_unplaned
            )
            Availabilty_Minus_Planned = int(current_available_minutes) - int(
                planned_time
            )
            Available_time = (Availabilty_Minutes / Availabilty_Minus_Planned) * 100
            Final_Availabilty = round(Available_time, 2)
        except ZeroDivisionError:
            Final_Availabilty = 0
        try:
            Final_product = production_is - scrap_is
            Quality = (Final_product / production_is) * 100
            Final_Quality = round(Quality, 2)
        except ZeroDivisionError:
            Final_Quality = 0
        try:
            oee = (
                (Final_Availabilty / 100)
                * (Final_performance / 100)
                * (Final_Quality / 100)
                * 100
            )
            Final_OEE = round(oee, 2)
        except ZeroDivisionError:
            Final_OEE = 0

        start_datetime = datetime.combine(datetime.today(), ShiftTimeStart_obj)
        end_datetime = datetime.combine(datetime.today(), ShiftTimeStop_obj)

        production_data111 = OEEData.objects.filter(DateTime__gte=start_datetime)
        data_list = []
        for record in production_data111:
            record_data = {
                "ID": record.id,
                "Production": record.Production,
                "DateTime": record.DateTime,
                "Scrap": record.Defective,
            }
            data_list.append(record_data)
        first_value = data_list[0] if data_list else None
        if first_value:
            filtered_data_list = []
            time_interval = timedelta(minutes=30)
            start_time = first_value["DateTime"]
            for item in data_list:
                if item["DateTime"] == start_time:
                    filtered_data_list.append(item)
                    start_time += time_interval
            production_values = []
            datetime_values = []
            defective_values = []

            for item in filtered_data_list:
                production_values.append(item["Production"])
                defective_values.append(item["Scrap"])
                datetime_obj = item["DateTime"]
                formatted_time = datetime_obj.strftime("%H:%M")
                datetime_values.append(formatted_time)
            last_production_values = production_values[-5:]
            last_datetime_values = datetime_values[-5:]
            last_defective_values = defective_values[-5:]
        else:
            last_production_values = [0]
            last_datetime_values = ["00:00"]
            last_defective_values = [0]
        target_left = int(target) - int(production_is)
        Error_statistics = {}  # To store error statistics dynamically

        # Get all unique error types from ErrorLabel
        error_labels = (
            Errorlabels.objects.all()
        )  # Assuming `ErrorLabel` is your table/model for error labels

        # Loop through each error type and calculate stats
        for label in error_labels:
            error_name = label.ErrorName
            error_bit = label.ErrorBit

            # Fetch error data for the specific error name
            error_data = ErrorDb.objects.filter(
                NameOfAlarm=error_name, Timing__date=today
            )
            true_timestamp = None
            false_timestamp = None
            time_differences = []

            # Calculate time differences for each error occurrence
            for record in error_data:
                if record.Alarm_value == "True":
                    true_timestamp = record.Timing
                elif record.Alarm_value == "False":
                    false_timestamp = record.Timing
                    if true_timestamp and false_timestamp:
                        difference = false_timestamp - true_timestamp
                        time_differences.append(int(difference.total_seconds() // 60))

            # Store aggregated statistics in a dictionary
            Error_statistics[error_name] = {
                "total_time": sum(time_differences),
                "occurrences": len(time_differences),
                "time_differences": time_differences,
            }
        print(Error_statistics, "error")
        # Aggregate all error times for break duration

        if total_break_duration is not None:
            Formattedtotal_break_duration = (
                (datetime.min + total_break_duration).time().strftime("%H:%M")
            )
        Formattedtotal_break_durationMinutes = int(
            total_break_duration.total_seconds() / 60
        )
        # Total_Available_shift_Time_Percentage = (
        #     TotalAvailableShifttimeMinutes / TotalShiftTimeinMinutes
        # ) * 100
        # Planned_Time_Percentage = (
        #     Formattedtotal_break_durationMinutes / TotalShiftTimeinMinutes
        # ) * 100
        Unplanned_Time_Percentage = (Final_unplaned / TotalShiftTimeinMinutes) * 100
        time.sleep(1)


def dataThreading():
    job_thread_data = threading.Thread(target=to_read_data)
    job_thread_data.start()


def ReportPage(request):
    return render(request, "report.html")


def ReportData(request):
    global weekdays, Dbis
    if request.method == "POST":
        datais = request.POST.get("start2")
        dt = request.POST.get("name13")
        oe = request.POST.get("name12")
        Dbis = FinalOeeData if dt is None else ErrorDb
    startdate = date.today()
    StartDateForWeeksList = str(startdate)

    if datais == "week":
        enddate = startdate - timedelta(days=7)
    elif datais == "month":
        enddate = startdate - timedelta(days=31)
    elif datais == "half_year":
        enddate = startdate - timedelta(days=180)
    elif datais == "year":
        enddate = startdate - timedelta(days=365)
    else:
        enddate = startdate - timedelta(
            days=7
        )  # Default to a week if datais is not recognized.

    EndDateForWeeksList = str(enddate)

    if dt is None:
        weekdays = Dbis.objects.values().filter(
            logged_on__date__range=[EndDateForWeeksList, StartDateForWeeksList]
        )
    else:
        weekdays = Dbis.objects.values().filter(
            Timing__date__range=[EndDateForWeeksList, StartDateForWeeksList]
        )

    weekdays = weekdays if weekdays else 0
    context = {
        "weekdays": weekdays,
    }
    return render(request, "report.html", context)


def Exporttopdf(response, data_type):

    response = HttpResponse(content_type="application/pdf")
    current_date = date.today().strftime("%Y-%m-%d")
    if data_type == "group_data":
        file_name = f"Downtime_Today_Report_{current_date}.pdf"
    else:
        if Dbis == FinalOeeData:
            file_name = f"OEE_Report_{current_date}.pdf"
        else:
            file_name = f"Downtime_Report_{current_date}.pdf"

    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    if data_type == "group_data":
        table_data = [
            ["Alarm", "Start time", "Stop time", "Timing"]
        ]  # Replace with actual column names
        for day in grouped_data:
            table_data.append(
                [
                    day["alarm"],
                    day["start_time"],
                    day["stop_time"],
                    day["time_difference"],
                ]
            )  #

    else:
        if Dbis == FinalOeeData:
            table_data = [
                ["Production", "Performance", "Availability", "Quality", "OEE", "Date"]
            ]  # Replace with actual column names
            for day in weekdays:
                formatted_date = day["logged_on"].strftime("%Y-%m-%d")
                table_data.append(
                    [
                        day["production"],
                        day["performance"],
                        day["availability"],
                        day["quality"],
                        day["oee"],
                        formatted_date,
                    ]
                )

        else:
            table_data = [
                ["Alarm", "Alarm Status", "Timing"]
            ]  # Replace with actual column names
            for day in weekdays:
                table_data.append(
                    [day["NameOfAlarm"], day["Alarm_value"], day["Timing"]]
                )  #

    image_path = "C:\\Users\\choud\\Downloads\\homework~\\oee_dashboard\\oee_dashboard_app\\static\\images\\technovizL.png"
    image = Image(image_path, width=100, height=100, hAlign="LEFT")
    elements.append(image)
    styles = getSampleStyleSheet()
    if data_type == "group_data":
        heading_text = "Today's Downtime Report"
    else:
        if Dbis == FinalOeeData:
            heading_text = "Production Effeciency Report"
        else:
            heading_text = "Downtime Report"
    heading = Paragraph(heading_text, styles["Title"])
    heading.alignment = TA_CENTER
    elements.append(heading)
    spacer = Spacer(50, 40)
    elements.append(spacer)
    table = Table(table_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(table)
    doc.build(elements, onFirstPage=add_border, onLaterPages=add_border)
    return response


def add_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.rect(20, 20, 570, 750)
    canvas.restoreState()


def downtimepage(request):
    global grouped_data

    today = date.today()
    data_for_today = ErrorDb.objects.filter(Timing__date=today)

    grouped_data = []

    for item in data_for_today:
        name_of_alarm = item.NameOfAlarm
        timing = item.Timing

        existing_entry = next(
            (
                entry
                for entry in grouped_data
                if entry["alarm"] == name_of_alarm and entry["stop_time"] is None
            ),
            None,
        )

        if existing_entry:
            existing_entry["stop_time"] = timing
        else:
            grouped_data.append(
                {"alarm": name_of_alarm, "start_time": timing, "stop_time": None}
            )

    # Calculate the time difference and add it to the grouped_data dictionary
    for entry in grouped_data:
        if entry["stop_time"] is not None:
            start_time = entry["start_time"]
            stop_time = entry["stop_time"]
            time_difference = stop_time - start_time
            entry["time_difference"] = time_difference

    today = datetime.today()
    seven_days_ago = today - timedelta(days=7)

    # Filter alarms for the last 7 days
    alarms = ErrorDb.objects.filter(Timing__range=[seven_days_ago, today])

    # Process the alarms to calculate durations and counts
    alarm_durations = {}
    alarm_counts = {}
    for alarm in alarms:
        if alarm.Alarm_value == "True":
            # Increment count for this alarm
            alarm_counts[alarm.NameOfAlarm] = alarm_counts.get(alarm.NameOfAlarm, 0) + 1

            # Find the corresponding 'False' entry for the same alarm
            end_time = (
                alarms.filter(
                    NameOfAlarm=alarm.NameOfAlarm,
                    Alarm_value="False",
                    Timing__gt=alarm.Timing,
                )
                .order_by("Timing")
                .first()
            )

            if end_time:
                duration = (end_time.Timing - alarm.Timing).total_seconds()
                alarm_durations[alarm.NameOfAlarm] = (
                    alarm_durations.get(alarm.NameOfAlarm, 0) + duration
                )

    # Convert durations to minutes
    alarm_durations = {
        alarm: duration / 60 for alarm, duration in alarm_durations.items()
    }

    # Sort alarms by duration in descending order
    sorted_alarms = sorted(alarm_durations.items(), key=lambda x: x[1], reverse=True)

    # Get the top two alarms
    top_alarms = sorted_alarms[:2]  # Contains up to two alarms with their durations

    # Prepare data for context
    top_alarm_details = [
        {"alarm_name": alarm[0], "duration": alarm[1], "count": alarm_counts.get(alarm[0], 0)}
        for alarm in top_alarms
    ]

    # Debug print
    print(top_alarm_details, "this is the top alarms")

    context = {
        "grouped_data": grouped_data,
        "FormattedTotalShiftTime": FormattedTotalShiftTime,
        "FormattedTotalAvailableShifttime": FormattedTotalAvailableShifttime,
        "Formattedtotal_break_duration": Formattedtotal_break_duration,
        "formatted_final_unplaned": formatted_final_unplaned,
        "Formattedtotal_break_durationMinutes": Formattedtotal_break_durationMinutes,
        "Final_unplaned": Final_unplaned,
        "Unplanned_Time_Percentage": Unplanned_Time_Percentage,
        "TotalShiftTimeinMinutes": TotalShiftTimeinMinutes,
        "runtime": runtime,
        "Available_Run_Time": Available_Run_Time,
        "FormattedTotalAvailableRunTime": FormattedTotalAvailableRunTime,
        "top_alarm_details": top_alarm_details,  # List containing details of top alarms
    }

    return render(request, "downtime.html", context)


from django.core.serializers.json import DjangoJSONEncoder
import json


def downtime_data(request):
    global grouped_data
    today = date.today()
    data_for_today = ErrorDb.objects.filter(Timing__date=today)

    grouped_data = []

    for item in data_for_today:
        name_of_alarm = item.NameOfAlarm
        timing = item.Timing

        existing_entry = next(
            (
                entry
                for entry in grouped_data
                if entry["alarm"] == name_of_alarm and entry["stop_time"] is None
            ),
            None,
        )

        if existing_entry:
            existing_entry["stop_time"] = timing
        else:
            grouped_data.append(
                {"alarm": name_of_alarm, "start_time": timing, "stop_time": None}
            )

    for entry in grouped_data:
        if entry["stop_time"] is not None:
            start_time = entry["start_time"]
            stop_time = entry["stop_time"]
            time_difference = stop_time - start_time
            entry["time_difference"] = time_difference

    # Process Error_statistics into chart data
    error_statistics_new = {
        "labels": [],
        "durationData": [],
        "incidentsData": [],
    }

    for alarm, stats in Error_statistics.items():
        error_statistics_new["labels"].append(alarm)
        error_statistics_new["durationData"].append(sum(stats["time_differences"]))
        error_statistics_new["incidentsData"].append(stats["occurrences"])
    print(error_statistics_new)

    context = {
        "grouped_data": json.dumps(grouped_data, cls=DjangoJSONEncoder),
        "FormattedTotalShiftTime": FormattedTotalShiftTime,
        "FormattedTotalAvailableShifttime": FormattedTotalAvailableShifttime,
        "Formattedtotal_break_duration": Formattedtotal_break_duration,
        "formatted_final_unplaned": formatted_final_unplaned,
        "Formattedtotal_break_durationMinutes": Formattedtotal_break_durationMinutes,
        "Final_unplaned": Final_unplaned,
        "Unplanned_Time_Percentage": Unplanned_Time_Percentage,
        "TotalShiftTimeinMinutes": TotalShiftTimeinMinutes,
        "runtime": runtime,
        "Available_Run_Time": Available_Run_Time,
        "FormattedTotalAvailableRunTime": FormattedTotalAvailableRunTime,
        "Error_statistics": Error_statistics,
        "chart_data": error_statistics_new,  # Add chart data here
    }

    return JsonResponse(context)


def Downdetails(request):
    return render(request, "Downdetails.html")


last_five_acceptedP1 = []


def foractualval(request):
    global target, Production_data, Scrap_data, last_five_acceptedP1

    if target is not None and Production_data is not None and Scrap_data is not None:
        target_left1 = int(target) - int(Production_data)
        acceptedP1 = int(Production_data) - int(Scrap_data)

        # Add the current acceptedP1 value to the list
        last_five_acceptedP1.append(acceptedP1)

        # Keep only the last five values
        if len(last_five_acceptedP1) > 5:
            last_five_acceptedP1 = last_five_acceptedP1[-5:]

        accdata = {
            "Production_data": Production_data,
            "Scrap_data": Scrap_data,
            "target_left1": target_left1,
            "acceptedP1": acceptedP1,
            "Running_value": Running_value,
            # Include the list in the response
            "target": target,
            "flag_error": flag_error,
        }

        return JsonResponse(accdata)
    else:
        return JsonResponse({"error": "Target or Production_data is None"})


def add_error(request):
    error_data = Errorlabels.objects.all()

    # Extract field names dynamically
    headers = [field.name for field in Errorlabels._meta.fields]
    if request.method == "POST":
        if "delete_label" in request.POST:
            label_id = request.POST.get("label_id")
            if label_id:
                Errorlabels.objects.filter(id=label_id).delete()

            return render(
                request,
                "config_error.html",
                {
                    "message": "Errors Delete successfully!",
                    "error_data": error_data,
                    "headers": headers,
                },
            )
        # Retrieve lists of error names and error bits
        error_names = request.POST.getlist("error_name[]")
        error_bits = request.POST.getlist("error_bit[]")

        # Save each error to the databasemysql
        for name, bit in zip(error_names, error_bits):
            if name and bit:  # Ensure fields are not empty
                new_error = Errorlabels(ErrorName=name, ErrorBit=bit)
                new_error.save()

        # Redirect or provide success message if necessary

        return render(
            request,
            "config_error.html",
            {
                "message": "Errors saved successfully!",
                "error_data": error_data,
                "headers": headers,
            },
        )

    return render(
        request, "config_error.html", {"error_data": error_data, "headers": headers}
    )


def add_paremeter(request):
    paremeter_data = parameterlabel.objects.all()
    headers = [field.name for field in parameterlabel._meta.fields]
    if request.method == "POST":
        # Retrieve lists of error names and error bits
        running_bit_db = request.POST.get("runn")
        production_bit_db = request.POST.get("pro")
        scrap_bit_db = request.POST.get("scra")

        # Save each error to the database

        new_error = parameterlabel(
            runnig_bit=running_bit_db,
            production_bit=production_bit_db,
            scrap_bit=scrap_bit_db,
        )
        new_error.save()

        # Redirect or provide success message if necessary
        return render(
            request,
            "machine_parameter.html",
            {
                "paremeter_data": paremeter_data,
                "headers": headers,
            },
        )

    return render(
        request,
        "machine_parameter.html",
        {
            "paremeter_data": paremeter_data,
            "headers": headers,
        },
    )


def Alarmpage(request):
    # Get today's date
    today = datetime.today().date()

    # Filter records for today's data where Alarm_value is "True"
    true_alarms = ErrorDb.objects.filter(Timing__date=today, Alarm_value="True")

    # Prepare the data
    live_alarms = []
    for alarm in true_alarms:
        # Determine alarm status as "critical" if it has the value "True"
        status = "critical" if alarm.NameOfAlarm == "Overload" else "moderate"

        # Add alarm to the list with the time and status
        live_alarms.append(
            {
                "name": alarm.NameOfAlarm,
                "time": alarm.Timing.strftime("%H:%M"),  # Extract time as HH:MM
                "status": status,
            }
        )

    # Pass the data to the template
    return render(
        request,
        "alarm_page.html",
        {"live_alarms": live_alarms},
    )


from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import F

def filter_alarms(request):
    time_period = request.GET.get("time_period", "all")
    today = datetime.today()
    start_date = None

    # Determine the time range based on the selected time period
    if time_period == "today":
        start_date = today.date()
    elif time_period == "previous_week":
        start_date = (today - timedelta(days=7)).date()
    elif time_period == "last_month":
        start_date = (today - timedelta(days=30)).date()

    # Filter the data based on the time range
    if start_date:
        alarm_data = ErrorDb.objects.filter(Timing__date__gte=start_date)
    else:
        alarm_data = ErrorDb.objects.all()

    # Fetch fresh data for every request
    alarm_data = alarm_data.order_by('NameOfAlarm', 'Timing').values(
        'NameOfAlarm', 'Alarm_value', 'Timing'
    )

    # Initialize a dictionary to store the results
    error_stats = defaultdict(lambda: {"total_time": 0, "occurrences": 0})
    alarm_pairs = defaultdict(list)

    # Group alarms by name and track active times
    for alarm in alarm_data:
        alarm_pairs[alarm['NameOfAlarm']].append((alarm['Alarm_value'], alarm['Timing']))

    # Calculate occurrences and total time
    for alarm_name, events in alarm_pairs.items():
        start_time = None
        for value, timing in events:
            if value == "True":
                start_time = timing
            elif value == "False" and start_time:
                # Calculate the duration and reset start_time
                duration = (timing - start_time).total_seconds() / 60
                error_stats[alarm_name]["total_time"] += duration
                error_stats[alarm_name]["occurrences"] += 1
                start_time = None  # Reset for the next pair

    # Prepare the response data
    response_data = {
        "incidents": [
            {"name": error, "occurrences": stats["occurrences"]}
            for error, stats in error_stats.items()
        ],
        "times": [
            {"name": error, "total_time": stats["total_time"]}
            for error, stats in error_stats.items()
        ],
    }

    return JsonResponse({"status": "success", "data": response_data})



def filter_production_data(request):
    today = date.today()
    production_records = OEEData.objects.filter(DateTime__date=today)
    alarm_record = ErrorDb.objects.filter(Timing__date=today)

    labels = []  # Timestamps for the X-axis
    production_data = []  # Production counts
    alarms = []  # Alarm data

    for record in production_records:
        labels.append(record.DateTime.strftime("%H:%M"))  # Format the time
        production_data.append(record.Production)  # Production count

    for alarm in alarm_record:
        alarms.append({
            "name": alarm.NameOfAlarm.lower(),
            "time": alarm.Timing.strftime("%H:%M"),
            "alarm": alarm.Alarm_value == 'True'
        })

    return JsonResponse({
        "status": "success",
        "labels": labels,
        "production": production_data,
        "alarms": alarms,
    })
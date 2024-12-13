from django.db import models
from datetime import datetime, date, timedelta
from django.utils import timezone


class Equipment(models.Model):
    name = models.CharField(max_length=100)


def current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def current_datetime1():
    return (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")


class OEEData(models.Model):
    DateTime = models.DateTimeField(default=current_datetime, blank=True, null=True)
    Production = models.IntegerField(max_length=50, blank=True, null=True)
    Defective = models.IntegerField(max_length=50, blank=True, null=True)
    Runtime_is = models.CharField(max_length=50, blank=True, null=True)
    Planed_time = models.CharField(max_length=50, blank=True, null=True)


class ShiftData(models.Model):
    Shift_Start = models.CharField(max_length=50)
    Shift_End = models.CharField(max_length=50)
    Tea_break_1_Start = models.CharField(max_length=50)
    Tea_break_1_Stop = models.CharField(max_length=50)
    lunch_break_start = models.CharField(max_length=50)
    lunch_break_stop = models.CharField(max_length=50)
    Tea_break_2_Start = models.CharField(max_length=50)
    Tea_break_2_Stop = models.CharField(max_length=50)


class PopupDataModel(models.Model):
    Descriptionis = models.CharField(max_length=50)
    BreakStartTime = models.CharField(max_length=50)
    BreakStopTime = models.CharField(max_length=50)
    EmailRequested = models.EmailField(max_length=50)
    Emailaproved = models.EmailField(max_length=50)


class FinalOeeData(models.Model):
    production = models.IntegerField(max_length=50, blank=True, null=True)
    performance = models.IntegerField(max_length=50, blank=True, null=True)
    availability = models.CharField(max_length=50, blank=True, null=True)
    quality = models.CharField(max_length=50, blank=True, null=True)
    oee = models.CharField(max_length=50, blank=True, null=True)
    logged_on = models.DateTimeField(default=current_datetime1, blank=True, null=True)
    defec = models.IntegerField(max_length=50, blank=True, null=True)


class ErrorDb(models.Model):
    NameOfAlarm = models.CharField(max_length=100, blank=True, null=True)
    Alarm_value = models.CharField(max_length=100, blank=True, null=True)
    Timing = models.DateTimeField(default=current_datetime, blank=True, null=True)


class Errorlabels(models.Model):
    ErrorName = models.CharField(max_length=100, blank=True, null=True)
    ErrorBit = models.IntegerField(max_length=100, blank=True, null=True)


class parameterlabel(models.Model):
    runnig_bit = models.IntegerField(max_length=100, blank=True, null=True)
    production_bit = models.IntegerField(max_length=100, blank=True, null=True)
    scrap_bit = models.IntegerField(max_length=100, blank=True, null=True)

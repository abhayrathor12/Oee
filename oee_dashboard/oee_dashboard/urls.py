"""oee_dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from oee_dashboard_app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomePage, name="HomePage"),
    # path('DeatailPage', views.DeatailPage, name='DeatailPage'),
    path("Detailform", views.Detailform, name="Detailform"),
    path("popupData", views.popupData, name="popupData"),
    path("DeatailPageload", views.DeatailPageload, name="DeatailPageload"),
    path("DeleteBreak/<int:id>/", views.DeleteBreak, name="DeleteBreak"),
    path("ReportPage", views.ReportPage, name="ReportPage"),
    path("ReportData", views.ReportData, name="ReportData"),
    path("Exporttopdf/<str:data_type>/", views.Exporttopdf, name="Exporttopdf"),
    path("downtimepage", views.downtimepage, name="downtimepage"),
    path("Downdetails", views.Downdetails, name="Downdetails"),
    path("home_page", views.home_page, name="home_page"),
    path("downtime_data", views.downtime_data, name="downtime_data"),
    path("foractualval", views.foractualval, name="foractualval"),
    path("add_error", views.add_error, name="add_error"),
    path("add_paremeter", views.add_paremeter, name="add_paremeter"),
    path("Alarmpage", views.Alarmpage, name="Alarmpage"),
    path("filter-alarms", views.filter_alarms, name="filter_alarms"),
]

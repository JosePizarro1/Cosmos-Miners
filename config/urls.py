
from django.contrib import admin
from django.urls import path
from game.views import login_view, login_page, register, register_view, home_view, profile_view, profile_update, create_withdrawal, process_withdrawal, logout_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", login_page, name="login_page"),
    path("register/", register, name="register"),
    path("register/view/", register_view, name="register_view"),  # HTML
    path("home/", home_view, name="home"),
    path("login/", login_view, name="login_api"),
    path("profile/", profile_view, name="profile_view"),
    path("profile/update/", profile_update, name="profile_update"),
    path("withdrawals/create/", create_withdrawal, name="withdrawal_create"),
    path("withdrawals/process/<int:pk>/", process_withdrawal, name="withdrawal_process"),
    path("logout/", logout_view, name="logout"),

]

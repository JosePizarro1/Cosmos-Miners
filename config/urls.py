
from django.contrib import admin
from django.urls import path
from game.views import  login_view,login_page
from game.views import register, register_view,home_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", login_page, name="login_page"),
    path("register/", register, name="register"),
    path("register/view/", register_view, name="register_view"),  # HTML
    path("home/", home_view, name="home"),
    path("login/", login_view, name="login_api"),

]


from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from game.views import login_view, login_page, register, register_view, home_view, profile_view, profile_update, create_withdrawal, process_withdrawal, withdrawals_admin_view, admin_dashboard_view, admin_dashboard_stats, miners_admin_view, miners_admin_stats, miner_types_list, miner_type_create, miner_type_update, miner_type_toggle, user_miners_list, user_miner_create, user_miner_delete, miners_view, logout_view
from game.views_transports import transports_admin_view, transports_admin_stats, transport_types_list, transport_type_create, transport_type_update, transport_type_toggle, user_transports_list, user_transport_create, user_transport_delete, transports_view
from game.views_tools import tools_admin_view, tools_admin_stats, tool_types_list, tool_type_create, tool_type_update, tool_type_toggle, user_tools_list, user_tool_create, user_tool_delete, tools_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", login_page, name="login_page"),
    path("register/", register, name="register"),
    path("register/view/", register_view, name="register_view"),  # HTML
    path("home/", home_view, name="home"),
    path("login/", login_view, name="login_api"),
    path("miners/", miners_view, name="miners_view"),
    path("profile/", profile_view, name="profile_view"),
    path("profile/update/", profile_update, name="profile_update"),
    path("withdrawals/create/", create_withdrawal, name="withdrawal_create"),
    path("withdrawals/process/<int:pk>/", process_withdrawal, name="withdrawal_process"),
    path("withdrawals/admin/", withdrawals_admin_view, name="withdrawals_admin"),
    path("dashboard/admin/", admin_dashboard_view, name="admin_dashboard"),
    path("dashboard/admin/stats/", admin_dashboard_stats, name="admin_dashboard_stats"),
    path("dashboard/miners/", miners_admin_view, name="miners_admin"),
    path("dashboard/miners/stats/", miners_admin_stats, name="miners_admin_stats"),
    path("dashboard/miner-types/list/", miner_types_list, name="miner_types_list"),
    path("dashboard/miner-types/create/", miner_type_create, name="miner_type_create"),
    path("dashboard/miner-types/update/<int:pk>/", miner_type_update, name="miner_type_update"),
    path("dashboard/miner-types/toggle/<int:pk>/", miner_type_toggle, name="miner_type_toggle"),
    path("dashboard/user-miners/list/", user_miners_list, name="user_miners_list"),
    path("dashboard/user-miners/create/", user_miner_create, name="user_miner_create"),
    path("dashboard/user-miners/delete/<int:pk>/", user_miner_delete, name="user_miner_delete"),
    path("transports/", transports_view, name="transports_view"),
    path("dashboard/transports/", transports_admin_view, name="transports_admin"),
    path("dashboard/transports/stats/", transports_admin_stats, name="transports_admin_stats"),
    path("dashboard/transport-types/list/", transport_types_list, name="transport_types_list"),
    path("dashboard/transport-types/create/", transport_type_create, name="transport_type_create"),
    path("dashboard/transport-types/update/<int:pk>/", transport_type_update, name="transport_type_update"),
    path("dashboard/transport-types/toggle/<int:pk>/", transport_type_toggle, name="transport_type_toggle"),
    path("dashboard/user-transports/list/", user_transports_list, name="user_transports_list"),
    path("dashboard/user-transports/create/", user_transport_create, name="user_transport_create"),
    path("dashboard/user-transports/delete/<int:pk>/", user_transport_delete, name="user_transport_delete"),
    path("tools/", tools_view, name="tools_view"),
    path("dashboard/tools/", tools_admin_view, name="tools_admin"),
    path("dashboard/tools/stats/", tools_admin_stats, name="tools_admin_stats"),
    path("dashboard/tool-types/list/", tool_types_list, name="tool_types_list"),
    path("dashboard/tool-types/create/", tool_type_create, name="tool_type_create"),
    path("dashboard/tool-types/update/<int:pk>/", tool_type_update, name="tool_type_update"),
    path("dashboard/tool-types/toggle/<int:pk>/", tool_type_toggle, name="tool_type_toggle"),
    path("dashboard/user-tools/list/", user_tools_list, name="user_tools_list"),
    path("dashboard/user-tools/create/", user_tool_create, name="user_tool_create"),
    path("dashboard/user-tools/delete/<int:pk>/", user_tool_delete, name="user_tool_delete"),
    path("logout/", logout_view, name="logout"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

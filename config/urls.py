
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from game.views import login_view, login_page, register, register_view, home_view, chests_public_view, buy_chest, open_chest, profile_view, profile_update, create_withdrawal, process_withdrawal, withdrawals_admin_view, admin_dashboard_view, admin_dashboard_stats, miners_admin_view, miners_admin_stats, miner_types_list, miner_type_create, miner_type_update, miner_type_toggle, user_miners_list, user_miner_create, user_miner_delete, miners_view, logout_view, rankings_view, registration_rewards_admin_view, registration_rewards_list_api, registration_reward_create_api, registration_reward_update_api, registration_reward_delete_api, registration_reward_toggle_api
from game.views_transports import transports_admin_view, transports_admin_stats, transport_types_list, transport_type_create, transport_type_update, transport_type_toggle, user_transports_list, user_transport_create, user_transport_delete, transports_view
from game.views_tools import tools_admin_view, tools_admin_stats, tool_types_list, tool_type_create, tool_type_update, tool_type_toggle, user_tools_list, user_tool_create, user_tool_delete, tools_view
from game.views_chests import (
    chests_admin_view, chests_list, chest_create, 
    chest_update, chest_delete, chest_toggle, 
    chest_dependencies, category_list, category_create, 
    category_update, category_delete
)
from game.views_rankings import (
    seasons_admin_view, seasons_list, season_create, 
    season_update, season_delete, season_toggle_override,
    public_rankings_page, public_rankings_list, get_levels_api, 
    get_available_items_api, enter_level_api,
    season_levels_admin_list, level_create, level_update, level_delete,
    get_level_competitors_api, claim_rewards_api
)
from game.views_planets import (
    planets_admin, mining_dashboard, prepare_trip,
    start_mining_trip, collect_mining_trip
)
from game.views_oil import (
    oil_admin_view, oil_admin_stats, oil_types_list, 
    oil_type_create, oil_type_update, oil_type_toggle,
    user_oil_list, user_oil_delete, buy_oil_central, user_oil_view,
    claim_oil_barrels, user_oil_force_ready, start_refining, claim_refinement,
    user_oil_force_refine_ready
)
from game.views_trades import (
    trades_admin_view, trade_offers_list, trade_offer_create,
    trade_offer_update, trade_offer_toggle, user_trades_list,
    user_trade_delete, trades_public_view, start_trade,
    claim_trade, force_ready_trade
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", login_page, name="login_page"),
    path("register/", register, name="register"),
    path("register/view/", register_view, name="register_view"),  # HTML
    path("home/", home_view, name="home"),
    path("login/", login_view, name="login_api"),
    path("chests/", chests_public_view, name="chests_public"),
    path("chests/buy/<int:chest_id>/", buy_chest, name="buy_chest"),
    path("chests/open/<int:user_chest_id>/", open_chest, name="open_chest"),
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
    path("oil-centrals/", user_oil_view, name="user_oil_view"),
    path("oil-centrals/claim/<int:pk>/", claim_oil_barrels, name="claim_oil_barrels"),
    path("oil-centrals/refine/<int:pk>/", start_refining, name="start_refining"),
    path("oil-centrals/claim-refinement/<int:pk>/", claim_refinement, name="claim_refinement"),
    path("dashboard/transports/", transports_admin_view, name="transports_admin"),
    path("dashboard/transports/stats/", transports_admin_stats, name="transports_admin_stats"),
    path("dashboard/transport-types/list/", transport_types_list, name="transport_types_list"),
    path("dashboard/transport-types/create/", transport_type_create, name="transport_type_create"),
    path("dashboard/transport-types/update/<int:pk>/", transport_type_update, name="transport_type_update"),
    path("dashboard/transport-types/toggle/<int:pk>/", transport_type_toggle, name="transport_type_toggle"),
    path("dashboard/user-transports/list/", user_transports_list, name="user_transports_list"),
    path("dashboard/user-transports/create/", user_transport_create, name="user_transport_create"),
    path("dashboard/user-transports/delete/<int:pk>/", user_transport_delete, name="user_transport_delete"),
    
    # Registration Rewards
    path("dashboard/registration-rewards/", registration_rewards_admin_view, name="registration_rewards_admin"),
    path("dashboard/registration-rewards/list/", registration_rewards_list_api, name="registration_rewards_list_api"),
    path("dashboard/registration-rewards/create/", registration_reward_create_api, name="registration_reward_create_api"),
    path("dashboard/registration-rewards/update/<int:pk>/", registration_reward_update_api, name="registration_reward_update_api"),
    path("dashboard/registration-rewards/delete/<int:pk>/", registration_reward_delete_api, name="registration_reward_delete_api"),
    path("dashboard/registration-rewards/toggle/<int:pk>/", registration_reward_toggle_api, name="registration_reward_toggle_api"),

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
    path("rankings/", public_rankings_page, name="rankings"),
    path("rankings/list/", public_rankings_list, name="rankings_list_api"),
    path("rankings/levels/<int:season_id>/", get_levels_api, name="rankings_levels_api"),
    path("rankings/competitors/<int:level_id>/", get_level_competitors_api, name="rankings_competitors_api"),
    path("rankings/available-items/", get_available_items_api, name="available_items_api"),
    path("rankings/enter/", enter_level_api, name="enter_level_api"),
    path("rankings/claim/", claim_rewards_api, name="claim_rewards_api"),

    # Chests Admin
    path("dashboard/chests/", chests_admin_view, name="chests_admin"),
    path("dashboard/chests/list/", chests_list, name="chests_list_api"),
    path("dashboard/chests/create/", chest_create, name="chest_create_api"),
    path("dashboard/chests/update/<int:pk>/", chest_update, name="chest_update_api"),
    path("dashboard/chests/delete/<int:pk>/", chest_delete, name="chest_delete_api"),
    path("dashboard/chests/toggle/<int:pk>/", chest_toggle, name="chest_toggle_api"),
    path("dashboard/chests/dependencies/", chest_dependencies, name="chest_dependencies_api"),
    path("dashboard/chests/categories/list/", category_list, name="category_list_api"),
    path("dashboard/chests/categories/create/", category_create, name="category_create_api"),
    path("dashboard/chests/categories/update/<int:pk>/", category_update, name="category_update_api"),
    path("dashboard/chests/categories/delete/<int:pk>/", category_delete, name="category_delete_api"),

    # Seasons Admin
    path("dashboard/seasons/", seasons_admin_view, name="seasons_admin"),
    path("dashboard/seasons/list/", seasons_list, name="seasons_list_api"),
    path("dashboard/seasons/create/", season_create, name="season_create_api"),
    path("dashboard/seasons/update/<int:pk>/", season_update, name="season_update_api"),
    path("dashboard/seasons/delete/<int:pk>/", season_delete, name="season_delete_api"),
    path("dashboard/seasons/toggle/<int:pk>/", season_toggle_override, name="season_toggle_api"),

    # Levels Admin
    path("dashboard/seasons/levels/list/<int:season_id>/", season_levels_admin_list, name="season_levels_admin_list"),
    path("dashboard/seasons/levels/create/", level_create, name="level_create_api"),
    path("dashboard/seasons/levels/update/<int:pk>/", level_update, name="level_update_api"),
    path("dashboard/seasons/levels/delete/<int:pk>/", level_delete, name="level_delete_api"),

    # Planets & Minerals
    path("dashboard/planets/", planets_admin, name="planets_admin"),
    path("mining/", mining_dashboard, name="mining_dashboard"),
    path("mining/prepare/", prepare_trip, name="prepare_trip"),
    path("mining/start/", start_mining_trip, name="start_mining_trip"),
    path("mining/collect/<int:trip_id>/", collect_mining_trip, name="collect_mining_trip"),

    # Oil Centrals Admin
    path("dashboard/oil/", oil_admin_view, name="oil_admin"),
    path("dashboard/oil/stats/", oil_admin_stats, name="oil_admin_stats"),
    path("dashboard/oil-types/list/", oil_types_list, name="oil_types_list"),
    path("dashboard/oil-types/create/", oil_type_create, name="oil_type_create"),
    path("dashboard/oil-types/update/<int:pk>/", oil_type_update, name="oil_type_update"),
    path("dashboard/oil-types/toggle/<int:pk>/", oil_type_toggle, name="oil_type_toggle"),
    path("dashboard/user-oil/list/", user_oil_list, name="user_oil_list"),
    path("dashboard/user-oil/delete/<int:pk>/", user_oil_delete, name="user_oil_delete"),
    path("dashboard/user-oil/force-ready/<int:pk>/", user_oil_force_ready, name="user_oil_force_ready"),
    path("dashboard/user-oil/force-refine-ready/<int:pk>/", user_oil_force_refine_ready, name="user_oil_force_refine_ready"),
    path("oil/buy/<int:type_id>/", buy_oil_central, name="buy_oil_central"),

    # Trades Admin & Public
    path("dashboard/trades/", trades_admin_view, name="trades_admin"),
    path("dashboard/trades/offers/list/", trade_offers_list, name="trade_offers_list"),
    path("dashboard/trades/offers/create/", trade_offer_create, name="trade_offer_create"),
    path("dashboard/trades/offers/update/<int:pk>/", trade_offer_update, name="trade_offer_update"),
    path("dashboard/trades/offers/toggle/<int:pk>/", trade_offer_toggle, name="trade_offer_toggle"),
    path("dashboard/trades/users/list/", user_trades_list, name="user_trades_list"),
    path("dashboard/trades/users/delete/<int:pk>/", user_trade_delete, name="user_trade_delete"),
    path("dashboard/trades/users/force-ready/<int:pk>/", force_ready_trade, name="force_ready_trade"),
    
    path("trades/", trades_public_view, name="trades_public"),
    path("trades/start/<int:offer_id>/", start_trade, name="start_trade"),
    path("trades/claim/<int:trade_id>/", claim_trade, name="claim_trade"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

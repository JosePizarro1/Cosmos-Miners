from django.contrib import admin
from .models import (
    Profile, WithdrawalRequest, Chest, ChestCategory, ChestReward, UserChest,
    MinerType, TransportType, ToolType, Season, SeasonLevel, UserSeasonEntry, SeasonLevelRequirement,
    RegistrationReward
)




@admin.register(MinerType)
class MinerTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "rarity", "attempts", "is_active")
    search_fields = ("name",)

@admin.register(TransportType)
class TransportTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "rarity", "speed", "is_active")
    search_fields = ("name",)

@admin.register(ToolType)
class ToolTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "rarity", "bonus_pct", "is_active")
    search_fields = ("name",)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "wallet_metamask_bsc", "cosmos_gold", "created_at")
    search_fields = ("user__username", "wallet_metamask_bsc")


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at", "processed_at", "processed_by")
    list_filter = ("status",)
    search_fields = ("user__username",)

class ChestRewardInline(admin.TabularInline):
    model = ChestReward
    extra = 1
    autocomplete_fields = ['miner_reward', 'transport_reward', 'tool_reward']

@admin.register(ChestCategory)
class ChestCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)

@admin.register(Chest)
class ChestAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_in_store", "rewards_per_open")
    list_filter = ("category", "is_in_store")
    search_fields = ("name", "description")
    inlines = [ChestRewardInline]


@admin.register(UserChest)
class UserChestAdmin(admin.ModelAdmin):
    list_display = ("chest", "owner", "obtained_at", "opened")
    list_filter = ("opened", "obtained_at")
    search_fields = ("owner__user__username", "chest__name")

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "claim_rewards_at", "is_active_override")
    list_filter = ("is_active_override",)
    search_fields = ("name",)

@admin.register(SeasonLevel)
class SeasonLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "lock_duration_days")
    list_filter = ("season",)

@admin.register(SeasonLevelRequirement)
class SeasonLevelRequirementAdmin(admin.ModelAdmin):
    list_display = ("level", "requirement_type", "value")
    list_filter = ("requirement_type", "level__season")

@admin.register(UserSeasonEntry)
class UserSeasonEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "season", "level", "entered_at", "locked_until")
    list_filter = ("season", "level")
    search_fields = ("user__username",)
@admin.register(RegistrationReward)
class RegistrationRewardAdmin(admin.ModelAdmin):
    list_display = ("reward_type", "miner_type", "transport_type", "tool_type", "amount", "is_active")
    list_filter = ("reward_type", "is_active")

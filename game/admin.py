from django.contrib import admin
from .models import Profile, WithdrawalRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "wallet_metamask_bsc", "cosmos_gold", "created_at")
    search_fields = ("user__username", "wallet_metamask_bsc")


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at", "processed_at", "processed_by")
    list_filter = ("status",)
    search_fields = ("user__username",)


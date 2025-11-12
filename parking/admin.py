from django.contrib import admin
from .models import TwoWheelerEntry, FourWheelerEntry

@admin.register(TwoWheelerEntry)
class TwoWheelerEntryAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'vehicle_no', 'entry_time', 'exit_time', 'amount', 'is_parked']
    list_filter = ['entry_time', 'exit_time']
    search_fields = ['token_id', 'vehicle_no']
    readonly_fields = ['token_id', 'entry_time']
    list_per_page = 20
    
    def is_parked(self, obj):
        return obj.exit_time is None
    is_parked.boolean = True
    is_parked.short_description = 'Parked'

@admin.register(FourWheelerEntry)
class FourWheelerEntryAdmin(admin.ModelAdmin):
    list_display = ['token_id', 'vehicle_no', 'entry_time', 'exit_time', 'amount', 'is_parked']
    list_filter = ['entry_time', 'exit_time']
    search_fields = ['token_id', 'vehicle_no']
    readonly_fields = ['token_id', 'entry_time']
    list_per_page = 20
    
    def is_parked(self, obj):
        return obj.exit_time is None
    is_parked.boolean = True
    is_parked.short_description = 'Parked'
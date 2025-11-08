from django.contrib import admin
from .models import Session, ScanResult


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'target_hostname', 'target_os', 'status', 'start_time', 'end_time')
    list_filter = ('status', 'target_os', 'start_time')
    search_fields = ('target_hostname', 'session_id')
    readonly_fields = ('session_id', 'start_time')
    ordering = ('-start_time',)


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('target', 'os', 'timestamp', 'session')
    list_filter = ('os', 'timestamp')
    search_fields = ('target',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

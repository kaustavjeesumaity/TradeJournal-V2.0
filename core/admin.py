from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Account, Trade, Tag, TradeAttachment, Instrument, Session, ChecklistItem, Positive, Negative, DailyChecklistTemplate, DailyChecklistItem, UserDailyChecklistProgress, TradePlan, TradePlanAttachment, TradePlanEvent

admin.site.register(User, UserAdmin)
admin.site.register(Account)
admin.site.register(Trade)
admin.site.register(Tag)
admin.site.register(TradeAttachment)

class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Session)
admin.site.register(ChecklistItem)
admin.site.register(Positive)
admin.site.register(Negative)

class DailyChecklistItemInline(admin.TabularInline):
    model = DailyChecklistItem
    extra = 1

@admin.register(DailyChecklistTemplate)
class DailyChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'effective_date', 'created_at')
    inlines = [DailyChecklistItemInline]
    ordering = ('-effective_date',)

@admin.register(UserDailyChecklistProgress)
class UserDailyChecklistProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'date', 'checked', 'checked_at')
    list_filter = ('user', 'date', 'checked')
    search_fields = ('user__email', 'item__text')

class TradePlanAttachmentInline(admin.TabularInline):
    model = TradePlanAttachment
    extra = 1

class TradePlanEventInline(admin.TabularInline):
    model = TradePlanEvent
    extra = 1
    fields = ('timestamp', 'description', 'emotion', 'confidence', 'action')
    readonly_fields = ('timestamp',)

@admin.register(TradePlan)
class TradePlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'instrument', 'planned_at', 'status')
    list_filter = ('status', 'planned_at', 'instrument')
    search_fields = ('user__email', 'instrument__name', 'rationale')
    inlines = [TradePlanAttachmentInline, TradePlanEventInline]

@admin.register(TradePlanAttachment)
class TradePlanAttachmentAdmin(admin.ModelAdmin):
    list_display = ('trade_plan', 'uploaded_at')

@admin.register(TradePlanEvent)
class TradePlanEventAdmin(admin.ModelAdmin):
    list_display = ('trade_plan', 'timestamp', 'action', 'emotion', 'confidence')
    list_filter = ('action', 'emotion')
    search_fields = ('description',)

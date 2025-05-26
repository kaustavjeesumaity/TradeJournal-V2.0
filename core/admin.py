from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Account, Trade, Tag, TradeAttachment, Instrument

admin.site.register(User, UserAdmin)
admin.site.register(Account)
admin.site.register(Trade)
admin.site.register(Tag)
admin.site.register(TradeAttachment)

class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Instrument, InstrumentAdmin)

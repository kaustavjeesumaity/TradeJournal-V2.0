from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Account, Trade, Tag, TradeAttachment

admin.site.register(User, UserAdmin)
admin.site.register(Account)
admin.site.register(Trade)
admin.site.register(Tag)
admin.site.register(TradeAttachment)

from rest_framework import serializers
from .models import Account, Trade, TradeAttachment

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'balance', 'currency', 'created_at', 'mt5_account_number', 'mt5_server', 'mt5_last_fetch']

class TradeAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeAttachment
        fields = ['id', 'file', 'uploaded_at']

class TradeSerializer(serializers.ModelSerializer):
    attachments = TradeAttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = Trade
        fields = [
            'id', 'account', 'instrument', 'entry_price', 'exit_price',
            'entry_date', 'exit_date', 'quantity', 'notes', 'tags', 'attachments',
            'gross_pnl', 'charges', 'net_pnl'
        ]

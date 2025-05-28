from rest_framework import serializers
from .models import Account, Trade, TradeAttachment, Tag, Session, ChecklistItem, Positive, Negative

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'balance', 'currency', 'created_at', 'mt5_account_number', 'mt5_server', 'mt5_last_fetch']

class TradeAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeAttachment
        fields = ['id', 'file', 'uploaded_at']

class TradeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    session = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all(), allow_null=True)
    checklist = serializers.PrimaryKeyRelatedField(many=True, queryset=ChecklistItem.objects.all())
    positives = serializers.PrimaryKeyRelatedField(many=True, queryset=Positive.objects.all())
    negatives = serializers.PrimaryKeyRelatedField(many=True, queryset=Negative.objects.all())
    attachments = TradeAttachmentSerializer(many=True, read_only=True)
    class Meta:
        model = Trade
        fields = '__all__'

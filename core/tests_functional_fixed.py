import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Trade, TradeAttachment, TradePlan, TradePlanAttachment
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class TradingJournalFunctionalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass123')
        self.account = self.user.accounts.create(name='TestAcc', balance=1000, currency='USD')
        self.client.login(username='testuser@example.com', password='testpass123')

    def test_add_trade(self):
        url = reverse('trade_create')
        data = {
            'account': self.account.pk,
            'instrument': 'AAPL',
            'entry_price': 100,
            'exit_price': 110,
            'entry_date': '2025-05-28 10:00',
            'exit_date': '2025-05-28 15:00',
            'size': 10,
            'notes': 'Test trade',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Trade.objects.filter(instrument='AAPL').exists())

    def test_edit_trade(self):
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', size=10)
        url = reverse('trade_edit', args=[trade.pk])
        data = {
            'account': trade.account.pk,
            'instrument': 'AAPL',
            'entry_price': 100,
            'exit_price': 120,
            'entry_date': '2025-05-28 10:00',
            'exit_date': '2025-05-28 15:00',
            'size': 10,
            'notes': 'Edited trade',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        trade.refresh_from_db()
        self.assertEqual(trade.exit_price, 120)

    def test_delete_trade(self):
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', size=10)
        url = reverse('trade_delete', args=[trade.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Trade.objects.filter(pk=trade.pk).exists())

    def test_add_trade_attachment(self):
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', size=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('trade_edit', args=[trade.pk])
        file_data = SimpleUploadedFile('test.txt', b'file_content')
        data = {
            'account': self.account.pk,
            'instrument': 'EURUSD',
            'entry_price': 1.1,
            'exit_price': 1.2,
            'entry_date': '2024-01-01T10:00',
            'exit_date': '2024-01-01T12:00',
            'size': 1,
            'notes': 'Test trade',
            'gross_pnl': 100,
            'charges': 10,
        }
        # Initial save
        response = self.client.post(url, data, follow=True)
        # Now upload attachment as a list
        data['attachments'] = [file_data]
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TradeAttachment.objects.filter(trade=trade).exists())

    def test_delete_trade_attachment(self):
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', size=10)
        attachment = TradeAttachment.objects.create(trade=trade, file=SimpleUploadedFile('testfile.txt', b'file_content'))
        url = reverse('delete_trade_attachment', args=[attachment.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TradeAttachment.objects.filter(pk=attachment.pk).exists())

    def test_create_trade_plan(self):
        url = reverse('trade_plan_create')
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        data = {
            'instrument': instr.pk,
            'planned_entry': 100,
            'planned_stop': 90,
            'planned_target': 120,
            'planned_size': 10,
            'checklist_template': '',
            'custom_checklist': '',
            'rationale': 'Test plan',
            'status': 'planned',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TradePlan.objects.filter(instrument=instr).exists())

    def test_create_trade_plan_with_event(self):
        url = reverse('trade_plan_create')
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        data = {
            'instrument': instr.pk,
            'planned_entry': 100,
            'planned_stop': 90,
            'planned_target': 120,
            'planned_size': 10,
            'checklist_template': '',
            'custom_checklist': '',
            'rationale': 'Test plan',
            'status': 'planned',
            'description': 'Initial thoughts',
            'emotion': 'Confident',
            'confidence': 8,
            'action': 'Planned',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        trade_plan = TradePlan.objects.filter(instrument=instr).first()
        self.assertIsNotNone(trade_plan)

    def test_upload_trade_plan_attachment(self):
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        trade_plan = TradePlan.objects.create(
            user=self.user,
            instrument=instr,
            planned_entry=100,
            planned_stop=90,
            planned_target=120,
            planned_size=10,
            rationale='Test plan'
        )
        url = reverse('trade_plan_edit', args=[trade_plan.pk])
        
        file_data = SimpleUploadedFile('planfile.txt', b'plan_file_content')
        
        data = {
            'instrument': instr.pk,
            'planned_entry': 100,
            'planned_stop': 90,
            'planned_target': 120,
            'planned_size': 10,
            'checklist_template': '',
            'custom_checklist': '',
            'rationale': 'Test plan',
            'status': 'planned',
            'attachments': file_data,
        }
        
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TradePlanAttachment.objects.filter(trade_plan=trade_plan).exists())

    def test_access_dashboard(self):
        """Test that the dashboard loads properly"""
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', size=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EURUSD')

    def test_analytics_view(self):
        """Test that analytics view works"""
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', size=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('advanced_analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_trade_detail_view(self):
        """Test trade detail view"""
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', size=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('trade_detail', args=[trade.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EURUSD')

    def test_trade_export_csv(self):
        """Test CSV export functionality"""
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', size=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('trade_export_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_trade_import_csv(self):
        """Test CSV import functionality"""
        csv_content = f"account,instrument,entry_price,exit_price,entry_date,exit_date,size,notes\n{self.account.name},EURUSD,1.1,1.2,2024-01-01T10:00,2024-01-01T12:00,1,Test trade"
        csv_file = SimpleUploadedFile('trades.csv', csv_content.encode('utf-8'), content_type='text/csv')
        
        url = reverse('trade_import_csv')
        data = {'csv_file': csv_file}
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Trade.objects.filter(instrument='EURUSD').exists())

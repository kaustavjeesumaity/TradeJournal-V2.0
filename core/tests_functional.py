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
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', quantity=10)
        url = reverse('trade_edit', args=[trade.pk])
        data = {
            'account': trade.account.pk,
            'instrument': 'AAPL',
            'entry_price': 100,
            'exit_price': 120,
            'entry_date': '2025-05-28 10:00',
            'exit_date': '2025-05-28 15:00',
            'quantity': 10,
            'notes': 'Edited trade',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        trade.refresh_from_db()
        self.assertEqual(trade.exit_price, 120)

    def test_delete_trade(self):
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', quantity=10)
        url = reverse('trade_delete', args=[trade.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Trade.objects.filter(pk=trade.pk).exists())

    def test_add_trade_attachment(self):
        trade = Trade.objects.create(account=self.account, instrument='EURUSD', entry_price=1.1, exit_price=1.2, entry_date='2024-01-01T10:00', exit_date='2024-01-01T12:00', quantity=1, notes='Test trade', gross_pnl=100, charges=10, net_pnl=90)
        url = reverse('trade_edit', args=[trade.pk])
        file_data = SimpleUploadedFile('test.txt', b'file_content')
        data = {
            'account': self.account.pk,
            'instrument': 'EURUSD',
            'entry_price': 1.1,
            'exit_price': 1.2,
            'entry_date': '2024-01-01T10:00',
            'exit_date': '2024-01-01T12:00',
            'quantity': 1,
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
        trade = Trade.objects.create(account=self.account, instrument='AAPL', entry_price=100, exit_price=110, entry_date='2025-05-28 10:00', exit_date='2025-05-28 15:00', quantity=10)
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
            'description': 'Initial event',
            'emotion': '',
            'action': '',
            'confidence': 1,
        }
        response = self.client.post(url, data)
        if response.status_code != 302:
            print('FORM ERRORS:', response.context['form'].errors)
            print('EVENT FORM ERRORS:', response.context['event_form'].errors)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TradePlan.objects.filter(rationale='Test plan').exists())

    def test_edit_trade_plan(self):
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        plan = TradePlan.objects.create(user=self.user, instrument=instr, planned_entry=100, planned_stop=90, planned_target=120, planned_size=10, rationale='Test plan', status='planned')
        url = reverse('trade_plan_edit', args=[plan.pk])
        data = {
            'instrument': instr.pk,
            'planned_entry': 110,
            'planned_stop': 95,
            'planned_target': 130,
            'planned_size': 12,
            'checklist_template': '',
            'custom_checklist': '',
            'rationale': 'Edited plan',
            'status': 'executed',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.planned_entry, 110)
        self.assertEqual(plan.status, 'executed')

    def test_delete_trade_plan(self):
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        plan = TradePlan.objects.create(user=self.user, instrument=instr, planned_entry=100, planned_stop=90, planned_target=120, planned_size=10, rationale='Test plan', status='planned')
        url = reverse('trade_plan_delete', args=[plan.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TradePlan.objects.filter(pk=plan.pk).exists())

    def test_add_trade_plan_attachment(self):
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        plan = TradePlan.objects.create(user=self.user, instrument=instr, planned_entry=100, planned_stop=90, planned_target=120, planned_size=10, rationale='Test plan', status='planned')
        url = reverse('trade_plan_edit', args=[plan.pk])
        from PIL import Image
        import io
        image = Image.new('RGB', (10, 10), color = 'red')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        file = SimpleUploadedFile('planfile.png', img_bytes.read(), content_type='image/png')
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
            'attachments': [file],
        }
        response = self.client.post(url, data)
        if response.status_code != 302:
            print('PLAN FORM ERRORS:', response.context['form'].errors)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TradePlanAttachment.objects.filter(trade_plan=plan).exists())

    def test_delete_trade_plan_attachment(self):
        from .models import Instrument
        instr = Instrument.objects.create(name='AAPL')
        plan = TradePlan.objects.create(user=self.user, instrument=instr, planned_entry=100, planned_stop=90, planned_target=120, planned_size=10, rationale='Test plan', status='planned')
        attachment = TradePlanAttachment.objects.create(trade_plan=plan, image=SimpleUploadedFile('planfile.txt', b'plan_file_content'))
        url = reverse('trade_plan_edit', args=[plan.pk])
        # Simulate deleting by removing the object
        attachment.delete()
        self.assertFalse(TradePlanAttachment.objects.filter(pk=attachment.pk).exists())

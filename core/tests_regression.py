from django.test import TestCase
from django.urls import reverse
from .models import User, Account, Trade, TradePlan, Instrument, Tag, Session, ChecklistItem, Positive, Negative, DailyChecklistTemplate, Milestone, Lesson, Achievement, Review, Course, Book, KeyLesson, Mistake
from django.utils import timezone

class RegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', username='testuser', password='testpass')
        self.account = Account.objects.create(user=self.user, name='Main', balance=10000, currency='USD')
        self.instrument = Instrument.objects.create(name='AAPL')
        self.tag = Tag.objects.create(name='Breakout')
        self.session = Session.objects.create(name='London')
        self.checklist_item = ChecklistItem.objects.create(name='Check news')
        self.positive = Positive.objects.create(name='Followed plan')
        self.negative = Negative.objects.create(name='Missed entry')
        self.template = DailyChecklistTemplate.objects.create(name='Default', effective_date=timezone.now().date())

    def test_tradeplan_crud(self):
        plan = TradePlan.objects.create(
            user=self.user,
            instrument=self.instrument,
            planned_entry=100,
            planned_stop=90,
            planned_target=120,
            planned_size=10,
            checklist_template=self.template,
            custom_checklist='Check news, Review risk',
            rationale='Test rationale',
            status='planned',
        )
        self.assertEqual(plan.user, self.user)
        self.assertEqual(plan.instrument, self.instrument)
        self.assertEqual(plan.status, 'planned')
        plan.status = 'executed'
        plan.save()
        self.assertEqual(TradePlan.objects.get(pk=plan.pk).status, 'executed')
        plan.delete()
        self.assertFalse(TradePlan.objects.filter(pk=plan.pk).exists())

    def test_trade_crud(self):
        trade = Trade.objects.create(
            account=self.account,
            instrument='AAPL',
            asset_class='Equity',
            direction='long',
            entry_price=100,
            exit_price=110,
            entry_date=timezone.now(),
            exit_date=timezone.now(),
            size=1,
            stop_loss=95,
            take_profit=115,
            risk_per_trade=100,
            fees=1,
            slippage=0.5,
            r_multiple=1.0,
            notes='Test trade',
            gross_pnl=10,
            charges=1,
            net_pnl=9,
            order_type='market',
            outcome='win',
            psychological_state='Calm',
            journal_notes='Good trade',
            lessons_learned='Stick to plan',
        )
        trade.tags.add(self.tag)
        trade.session = self.session
        trade.checklist.add(self.checklist_item)
        trade.positives.add(self.positive)
        trade.negatives.add(self.negative)
        trade.save()
        self.assertEqual(trade.account, self.account)
        self.assertEqual(trade.instrument, 'AAPL')
        self.assertEqual(trade.net_pnl, 9)
        trade.delete()
        self.assertFalse(Trade.objects.filter(pk=trade.pk).exists())

    def test_user_profile_fields(self):
        self.user.trading_style = 'day'
        self.user.experience_level = 'beginner'
        self.user.risk_profile = 'conservative'
        self.user.goals = 'Become profitable'
        self.user.save()
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.trading_style, 'day')
        self.assertEqual(user.experience_level, 'beginner')
        self.assertEqual(user.goals, 'Become profitable')

    def test_structured_learning_models(self):
        course = Course.objects.create(user=self.user, name='Trading 101', completed=True)
        book = Book.objects.create(user=self.user, title='Market Wizards', completed=True)
        keylesson = KeyLesson.objects.create(user=self.user, content='Cut losses quickly')
        mistake = Mistake.objects.create(user=self.user, description='Overtrading')
        self.assertTrue(Course.objects.filter(name='Trading 101').exists())
        self.assertTrue(Book.objects.filter(title='Market Wizards').exists())
        self.assertTrue(KeyLesson.objects.filter(content__icontains='Cut losses').exists())
        self.assertTrue(Mistake.objects.filter(description__icontains='Overtrading').exists())

    def test_milestone_lesson_achievement_review(self):
        milestone = Milestone.objects.create(description='First 100 trades')
        lesson = Lesson.objects.create(content='Always use stop loss', source='Book')
        achievement = Achievement.objects.create(name='Consistent month')
        review = Review.objects.create(period='monthly', summary='Good progress')
        self.assertTrue(Milestone.objects.filter(description='First 100 trades').exists())
        self.assertTrue(Lesson.objects.filter(content__icontains='stop loss').exists())
        self.assertTrue(Achievement.objects.filter(name='Consistent month').exists())
        self.assertTrue(Review.objects.filter(period='monthly').exists())

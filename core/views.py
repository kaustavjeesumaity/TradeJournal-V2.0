from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, AccountForm, TradeForm, MT5FetchForm, TradePlanForm, TradePlanEventForm,
    UserForm, MilestoneForm, LessonForm, AchievementForm, ReviewForm,
    CourseForm, BookForm, KeyLessonForm, MistakeForm, MT5AccountForm
)
from .models import Account, Trade, TradeAttachment, Instrument, DailyChecklistTemplate, DailyChecklistItem, UserDailyChecklistProgress, TradePlan, TradePlanAttachment, TradePlanEvent, TradePlanEventAttachment, Milestone, Lesson, Achievement, Review, Course, Book, KeyLesson, Mistake
from django.urls import reverse
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.utils.dateparse import parse_date
import csv
import sys
from django.http import HttpResponse
from django.contrib import messages
from decimal import Decimal
from django.core.paginator import Paginator
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
from rest_framework import viewsets, permissions
from .serializers import AccountSerializer, TradeSerializer
import datetime
from django.utils import timezone
from calendar import monthrange, Calendar
from datetime import timedelta, date, datetime

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    accounts = Account.objects.filter(user=request.user)
    
    # Handle account selection
    selected_account_id = request.GET.get('account') or request.session.get('selected_account_id')
    selected_account = None
    
    if selected_account_id:
        try:
            selected_account = accounts.get(id=selected_account_id)
            request.session['selected_account_id'] = selected_account_id
        except Account.DoesNotExist:
            pass
    
    if not selected_account and accounts.exists():
        selected_account = accounts.first()
        request.session['selected_account_id'] = selected_account.id
    
    # Only show trades for the selected account if one is selected
    if selected_account:
        trades = Trade.objects.filter(account=selected_account)
    else:
        trades = Trade.objects.filter(account__user=request.user)

    # Filtering (account selection is now only via navbar, not filter form)
    instrument = request.GET.getlist('instrument')
    outcome = request.GET.get('outcome', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort = request.GET.get('sort', 'exit_date')

    # Handle 'ALL' for multi-select
    if instrument and 'ALL' not in instrument:
        trades = trades.filter(instrument__in=instrument)
    # If 'ALL' is selected or nothing is selected, do not filter by instrument

    if outcome == 'win':
        trades = trades.filter(exit_price__gt=F('entry_price'))
    elif outcome == 'loss':
        trades = trades.filter(exit_price__lt=F('entry_price'))
    if start_date:
        trades = trades.filter(exit_date__date__gte=parse_date(start_date))
    if end_date:
        trades = trades.filter(exit_date__date__lte=parse_date(end_date))
    if sort:
        trades = trades.order_by(sort)

    # Pagination
    paginator = Paginator(trades, 10)  # Show 10 trades per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Currency conversion
    base_currency = request.GET.get('base_currency', 'USD')
    conversion_rates = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'JPY': 156.0,
        'CAD': 1.36,
    }
    # Account summaries with conversion
    account_summaries = []
    for account in accounts:
        account_trades = trades.filter(account=account)
        account_pnl = sum([t.pnl or 0 for t in account_trades])
        rate = conversion_rates.get(account.currency, 1.0) / conversion_rates.get(base_currency, 1.0)
        account_summary = {
            'name': account.name,
            'balance': account.balance,
            'currency': account.currency,
            'pnl': account_pnl,
            'converted_balance': float(account.balance) * rate,
            'converted_pnl': float(account_pnl) * rate,
        }
        account_summaries.append(account_summary)
        
    # Summary statistics
    total_pnl = sum([t.pnl or 0 for t in trades])
    total_trades = trades.count()
    wins = trades.filter(exit_price__gt=F('entry_price')).count()
    losses = trades.filter(exit_price__lt=F('entry_price')).count()
    win_rate = (wins / total_trades * 100) if total_trades else 0
    avg_risk_reward = (
        sum([
            ((t.exit_price or Decimal(0)) - (t.entry_price or Decimal(0))) / abs(t.entry_price)
            for t in trades
            if t.entry_price is not None and t.exit_price is not None
        ]) / total_trades
        if total_trades else 0
    )
    pnl_dates = [t.exit_date.strftime('%Y-%m-%d') for t in trades.order_by('exit_date') if t.exit_date]
    pnl_values = [float(t.pnl or 0) for t in trades.order_by('exit_date')]

    # Instrument analytics
    instrument_stats = []
    instrument_map = defaultdict(list)
    for t in trades:
        instrument_map[t.instrument].append(t)
    for instrument_name, tlist in instrument_map.items():
        count = len(tlist)
        wins = sum([1 for t in tlist if t.pnl and t.pnl > 0])
        pnl = sum([t.pnl or 0 for t in tlist])
        win_rate_inst = (wins / count * 100) if count else 0
        instrument_stats.append({
            'instrument': instrument_name,
            'count': count,
            'win_rate': win_rate_inst,
            'pnl': pnl,
        })
    # Outcome analytics
    outcome_stats = []
    for outcome_label, filter_func in [
        ("Win", lambda t: t.pnl and t.pnl > 0),
        ("Loss", lambda t: t.pnl and t.pnl < 0),
        ("Break-even", lambda t: t.pnl and t.pnl == 0),
    ]:
        tlist = [t for t in trades if filter_func(t)]
        count = len(tlist)
        wins = len([t for t in tlist if t.exit_price > t.entry_price])
        pnl = sum([t.pnl or 0 for t in tlist])
        win_rate_outcome = (wins / count * 100) if count else 0
        outcome_stats.append({
            'outcome': outcome_label,
            'count': count,
            'win_rate': win_rate_outcome,
            'pnl': pnl,
        })

    instrument_list = list(Instrument.objects.values_list('name', flat=True).order_by('name'))
    account_options = [(account.pk, account.name) for account in accounts]
    default_account = account_options[0][0] if account_options else ''
    filter_dict = {
        'instrument': instrument,
        'outcome': outcome,
        'start_date': start_date,
        'end_date': end_date,
        'sort': sort,
    }

    return render(request, 'dashboard.html', {
        'accounts': accounts,
        'selected_account': selected_account,
        'account_summaries': account_summaries,
        'trades': page_obj.object_list if 'page_obj' in locals() else trades,
        'page_obj': page_obj if 'page_obj' in locals() else None,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'avg_risk_reward': avg_risk_reward,
        'pnl_dates': pnl_dates,
        'pnl_values': pnl_values,
        'filter': filter_dict,
        'base_currency': base_currency,
        'conversion_rates': conversion_rates,
        'instrument_stats': instrument_stats,
        'outcome_stats': outcome_stats,
        'instrument_list': instrument_list,
        'account_options': account_options,
        'default_account': default_account,
    })

@login_required
def advanced_analytics_view(request):
    accounts = Account.objects.filter(user=request.user)
    selected_account_id = request.GET.get('account') or request.session.get('selected_account_id')
    selected_account = None
    if selected_account_id:
        try:
            selected_account = accounts.get(id=selected_account_id)
        except Account.DoesNotExist:
            pass
    if not selected_account and accounts.exists():
        selected_account = accounts.first()
    # Only show trades for the selected account if one is selected
    if selected_account:
        trades = Trade.objects.filter(account=selected_account)
    else:
        trades = Trade.objects.filter(account__user=request.user)

    # Filtering (reuse dashboard logic for consistency, account selection is only via navbar)
    instrument = request.GET.getlist('instrument')
    outcome = request.GET.get('outcome', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort = request.GET.get('sort', 'exit_date')

    if instrument and 'ALL' not in instrument:
        trades = trades.filter(instrument__in=instrument)
    if outcome == 'win':
        trades = trades.filter(exit_price__gt=F('entry_price'))
    elif outcome == 'loss':
        trades = trades.filter(exit_price__lt=F('entry_price'))
    if start_date:
        trades = trades.filter(exit_date__date__gte=parse_date(start_date))
    if end_date:
        trades = trades.filter(exit_date__date__lte=parse_date(end_date))
    if sort:
        trades = trades.order_by(sort)

    # PnL over time
    pnl_dates = [t.exit_date.strftime('%Y-%m-%d') for t in trades.order_by('exit_date')]
    pnl_values = [float(t.net_pnl or 0) for t in trades.order_by('exit_date')]

    # Win/Loss ratio
    win_count = trades.filter(exit_price__gt=F('entry_price')).count()
    loss_count = trades.filter(exit_price__lt=F('entry_price')).count()
    win_loss_data = [win_count, loss_count]

    # Avg. holding period by instrument
    holding_map = defaultdict(list)
    for t in trades:
        holding_hours = (t.exit_date - t.entry_date).total_seconds() / 3600.0 if t.exit_date and t.entry_date else 0
        holding_map[t.instrument].append(holding_hours)
    holding_labels = list(holding_map.keys())
    holding_data = [round(sum(v)/len(v), 2) if v else 0 for v in holding_map.values()]    # Tag performance
    tag_map = defaultdict(list)
    for t in trades:
        if hasattr(t, 'tags'):
            for tag in t.tags.all():
                tag_map[str(tag)].append(t.net_pnl or 0)
    tag_labels = list(tag_map.keys())
    tag_data = [round(sum(v), 2) for v in tag_map.values()]    # Session performance
    session_map = defaultdict(list)
    for t in trades:
        session = getattr(t, 'session', None)
        if session:
            session_map[str(session)].append(t.net_pnl or 0)  # Use str(session) for JSON serializability
    session_labels = list(session_map.keys())
    session_data = [round(sum(v), 2) for v in session_map.values()]

    # Streaks
    streaks = {'longest_win': 0, 'longest_loss': 0, 'current': 0}
    current_streak = 0
    max_win = 0
    max_loss = 0
    last_result = None
    for t in trades.order_by('exit_date'):
        result = 'win' if t.exit_price > t.entry_price else 'loss' if t.exit_price < t.entry_price else 'break'
        if result == last_result and result != 'break':
            current_streak += 1
        else:
            current_streak = 1 if result != 'break' else 0
        if result == 'win':
            max_win = max(max_win, current_streak)
        elif result == 'loss':
            max_loss = max(max_loss, current_streak)
        last_result = result
    streaks['longest_win'] = max_win
    streaks['longest_loss'] = max_loss
    streaks['current'] = current_streak

    # Best/worst trades
    best_trade = trades.order_by('-net_pnl').first()
    worst_trade = trades.order_by('net_pnl').first()
    # Milestones (example: 10th, 50th, 100th trade, or custom logic)
    milestones = []
    trade_count = trades.count()
    for m in [10, 50, 100, 250, 500, 1000]:
        if trade_count >= m:
            milestones.append(f"{m} trades completed!")
    if best_trade:
        milestones.append(f"Best trade: {best_trade.instrument} ({best_trade.exit_date.strftime('%Y-%m-%d')}) PnL: {best_trade.net_pnl or 0:.2f}")
    if worst_trade:
        milestones.append(f"Worst trade: {worst_trade.instrument} ({worst_trade.exit_date.strftime('%Y-%m-%d')}) PnL: {worst_trade.net_pnl or 0:.2f}")

    return render(request, 'advanced_analytics.html', {
        'pnl_dates': pnl_dates,
        'pnl_values': pnl_values,
        'win_loss_data': win_loss_data,
        'holding_labels': holding_labels,
        'holding_data': holding_data,
        'tag_labels': tag_labels,
        'tag_data': tag_data,
        'session_labels': session_labels,
        'session_data': session_data,
        'streaks': streaks,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'milestones': milestones,
    })

@login_required
def account_create_view(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account_source = form.cleaned_data.get('account_source')
            if account_source == 'mt5':
                # Pass account name as GET param for pre-filling
                account_name = form.cleaned_data.get('name', '')
                return redirect(f"{reverse('mt5_account_connect')}?account_name={account_name}")
            else:
                # Create manual account
                account = form.save(commit=False)
                account.user = request.user
                account.save()
                messages.success(request, f'Account "{account.name}" created successfully!')
                return redirect('dashboard')
    else:
        form = AccountForm()
    return render(request, 'account_form.html', {'form': form})


@login_required 
def mt5_account_connect_view(request):
    """Handle MT5 account connection"""
    if request.method == 'POST':
        form = MT5AccountForm(request.POST)
        if form.is_valid():
            try:
                if mt5 is None:
                    messages.error(request, 'MetaTrader 5 library is not installed.')
                    return redirect('account_create')
                
                # Initialize MT5 connection
                if not mt5.initialize():
                    messages.error(request, 'Failed to initialize MetaTrader 5.')
                    return redirect('account_create')
                
                # Login to MT5
                login_result = mt5.login(
                    login=int(form.cleaned_data['mt5_account']),
                    server=form.cleaned_data['mt5_server'],
                    password=form.cleaned_data['mt5_password']
                )
                
                if login_result:
                    # Get account info
                    account_info = mt5.account_info()
                    if account_info:
                        # Create account with MT5 data
                        account = Account.objects.create(
                            user=request.user,
                            name=form.cleaned_data['account_name'],
                            broker=account_info.company,
                            account_type='demo' if 'demo' in form.cleaned_data['mt5_server'].lower() else 'real',
                            leverage=account_info.leverage,
                            equity=account_info.equity,
                            margin=account_info.margin,
                            balance=account_info.balance,
                            currency=account_info.currency,
                            mt5_account_number=form.cleaned_data['mt5_account'],
                            mt5_server=form.cleaned_data['mt5_server'],
                            mt5_last_fetch=timezone.now()
                        )
                        
                        messages.success(request, f'MT5 account "{account.name}" connected successfully!')
                        
                        # Optionally fetch recent trades
                        try:
                            fetch_mt5_trades_for_account(account)
                            messages.info(request, 'Recent trades have been imported from MT5.')
                        except Exception as e:
                            messages.warning(request, f'Account created but failed to import trades: {str(e)}')
                        
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'Failed to get account information from MT5.')
                else:
                    messages.error(request, 'Failed to login to MT5. Please check your credentials.')
                
                mt5.shutdown()
            except Exception as e:
                messages.error(request, f'Error connecting to MT5: {str(e)}')
    else:
        # Pre-fill account_name from GET param if present
        initial = {}
        account_name = request.GET.get('account_name')
        if account_name:
            initial['account_name'] = account_name
        form = MT5AccountForm(initial=initial)
        # Get existing MT5 accounts for the user
        existing_mt5_accounts = Account.objects.filter(
            user=request.user,
            mt5_account_number__isnull=False
        ).order_by('-mt5_last_fetch')
    return render(request, 'mt5_account_form.html', {
        'form': form,
        'existing_mt5_accounts': existing_mt5_accounts
    })

@login_required
def trade_create_view(request):
    if request.method == 'POST':
        form = TradeForm(request.POST, request.FILES)
        form.fields['account'].queryset = Account.objects.filter(user=request.user)
        if form.is_valid():
            trade = form.save(commit=False)
            # Calculate net_pnl if gross_pnl and charges are provided
            gross_pnl = form.cleaned_data.get('gross_pnl')
            charges = form.cleaned_data.get('charges')
            if gross_pnl is not None and charges is not None:
                trade.gross_pnl = gross_pnl
                trade.charges = charges
                trade.net_pnl = gross_pnl - charges
            if trade.account.user == request.user:
                trade.save()
                form.save_m2m()
                # Handle multiple attachments
                for f in request.FILES.getlist('attachments'):
                    TradeAttachment.objects.create(trade=trade, file=f)
                return redirect('dashboard')
            else:
                form.add_error('account', 'Invalid account selection.')
    else:
        form = TradeForm()
        form.fields['account'].queryset = Account.objects.filter(user=request.user)
    return render(request, 'trade_form.html', {'form': form})

@login_required
def account_edit_view(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = AccountForm(instance=account)
    return render(request, 'account_form.html', {'form': form, 'edit': True})

@login_required
def account_delete_view(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        return redirect('dashboard')
    return render(request, 'account_confirm_delete.html', {'account': account})

@login_required
def trade_edit_view(request, pk):
    trade = get_object_or_404(Trade, pk=pk, account__user=request.user)
    if request.method == 'POST':
        form = TradeForm(request.POST, request.FILES, instance=trade)
        form.fields['account'].queryset = Account.objects.filter(user=request.user)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Form non-field errors: {form.non_field_errors()}")
            for field, errors in form.errors.items():
                print(f"Field '{field}' errors: {errors}")
            # Also print form data for debugging
            print(f"Form data keys: {list(request.POST.keys())}")
            print(f"Form cleaned_data (partial): {getattr(form, 'cleaned_data', 'No cleaned_data')}")
        if form.is_valid():
            trade = form.save(commit=False)
            # Calculate net_pnl if gross_pnl and charges are not provided
            gross_pnl = form.cleaned_data.get('gross_pnl')
            charges = form.cleaned_data.get('charges')
            if gross_pnl is not None and charges is not None:
                trade.gross_pnl = gross_pnl
                trade.charges = charges
                trade.net_pnl = gross_pnl - charges
            if trade.account.user == request.user:
                trade.save()
                form.save_m2m()
                # Handle new attachments
                for f in request.FILES.getlist('attachments'):
                    TradeAttachment.objects.create(trade=trade, file=f)
                return redirect('trade_detail', pk=trade.pk)
            else:
                form.add_error('account', 'Invalid account selection.')
    else:
        form = TradeForm(instance=trade)
        form.fields['account'].queryset = Account.objects.filter(user=request.user)
    return render(request, 'trade_form.html', {'form': form, 'edit': True, 'trade': trade})

@login_required
def trade_delete_view(request, pk):
    trade = get_object_or_404(Trade, pk=pk, account__user=request.user)
    if request.method == 'POST':
        trade.delete()
        return redirect('dashboard')
    return render(request, 'trade_confirm_delete.html', {'trade': trade})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

@login_required
def trade_export_csv(request):
    trades = Trade.objects.filter(account__user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trades.csv"'
    writer = csv.writer(response)
    writer.writerow(['account', 'instrument', 'entry_price', 'exit_price', 'entry_date', 'exit_date', 'size', 'notes'])
    for t in trades:
        writer.writerow([
            t.account.name,
            t.instrument,
            t.entry_price,
            t.exit_price,
            t.entry_date,
            t.exit_date,
            t.size,
            t.notes
        ])
    return response

@login_required
def trade_import_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        accounts = {a.name: a for a in Account.objects.filter(user=request.user)}
        count = 0
        for row in reader:
            account = accounts.get(row['account'])
            if not account:
                continue
            Trade.objects.create(
                account=account,
                instrument=row['instrument'],
                entry_price=row['entry_price'],
                exit_price=row['exit_price'],
                entry_date=row['entry_date'],
                exit_date=row['exit_date'],
                size=row['size'],
                notes=row.get('notes', '')
            )
            count += 1
        messages.success(request, f"Imported {count} trades.")
        return redirect('dashboard')
    return render(request, 'trade_import.html')

@login_required
def position_size_calculator(request):
    position_size = None
    if request.method == 'POST':
        try:
            balance = float(request.POST.get('balance'))
            risk_pct = float(request.POST.get('risk_pct'))
            entry_price = float(request.POST.get('entry_price'))
            stop_price = float(request.POST.get('stop_price'))
            risk_amount = balance * (risk_pct / 100)
            per_unit_risk = abs(entry_price - stop_price)
            if per_unit_risk > 0:
                position_size = risk_amount / per_unit_risk
        except Exception:
            position_size = None
    return render(request, 'position_size_calculator.html', {'position_size': position_size})

@login_required
def fetch_mt5_trades(request):
    message = None
    trades_fetched = 0
    trades_updated = 0
    
    if request.method == 'POST':
        form = MT5FetchForm(user=request.user, data=request.POST)
        if form.is_valid():
            selected_account = form.cleaned_data['mt5_account']
            mt5_password = form.cleaned_data['mt5_password']
            
            if not mt5:
                message = 'MetaTrader5 package is not installed.'
            else:
                # Use the selected account's MT5 credentials
                mt5_account = selected_account.mt5_account_number
                mt5_server = selected_account.mt5_server
                
                # Initialize MT5
                if not mt5.initialize(server=mt5_server, login=int(mt5_account), password=mt5_password):
                    message = f"MT5 initialize() failed: {mt5.last_error()}"
                else:
                    # Fetch only trades after last fetch
                    from datetime import datetime, timezone
                    last_fetch = selected_account.mt5_last_fetch
                    if last_fetch:
                        from_date = last_fetch
                    else:
                        # If never fetched, fetch from 1 year ago
                        from_date = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year-1)
                    to_date = datetime.now(timezone.utc)
                    orders = mt5.history_deals_get(from_date, to_date)
                    if orders is None:
                        message = 'No trades found or error fetching trades.'
                    else:
                        latest_trade_time = last_fetch
                        # Aggregate deals into trades by position_id
                        deals_by_position = defaultdict(list)
                        for order in orders:
                            # Only consider buy/sell deals (type 0/1)
                            if hasattr(order, 'type') and order.type in (0, 1):
                                deals_by_position[getattr(order, 'position_id', None)].append(order)
                        
                        for position_id, deals in deals_by_position.items():
                            if not deals or position_id is None:
                                continue
                            # Sort deals by time
                            deals = sorted(deals, key=lambda d: d.time)
                            entry_deal = deals[0]
                            exit_deal = deals[-1]
                            
                            # Aggregate P&L and charges from all deals in this position
                            gross_pnl = sum(getattr(d, 'profit', 0) for d in deals)
                            charges = sum((getattr(d, 'commission', 0) or 0) + (getattr(d, 'swap', 0) or 0) + (getattr(d, 'fee', 0) or 0) for d in deals)
                            net_pnl = gross_pnl - charges
                            
                            # Convert times
                            entry_time = datetime.fromtimestamp(entry_deal.time, tz=timezone.utc) if isinstance(entry_deal.time, (int, float)) else entry_deal.time
                            exit_time = datetime.fromtimestamp(exit_deal.time, tz=timezone.utc) if isinstance(exit_deal.time, (int, float)) else exit_deal.time
                            
                            # Check if trade already exists (by position_id in notes)
                            existing_trade = Trade.objects.filter(account=selected_account, notes__contains=f"MT5 position: {position_id}").first()
                            
                            # Add instrument to Instrument model if not exists
                            instrument_name = getattr(entry_deal, 'symbol', '')
                            if instrument_name and not Instrument.objects.filter(name=instrument_name).exists():
                                Instrument.objects.create(name=instrument_name)
                            
                            if existing_trade:
                                # Update existing trade if it has changed (e.g., from open to closed)
                                # Determine if position is closed (more than one deal indicates closure)
                                is_closed = len(deals) > 1 and exit_time > entry_time
                                new_status = 'closed' if is_closed else 'open'
                                
                                # Check if the trade needs updating
                                needs_update = False
                                if existing_trade.status != new_status:
                                    existing_trade.status = new_status
                                    needs_update = True
                                
                                if is_closed and existing_trade.exit_price != getattr(exit_deal, 'price', 0):
                                    existing_trade.exit_price = getattr(exit_deal, 'price', 0)
                                    existing_trade.exit_date = exit_time
                                    needs_update = True
                                
                                # Update P&L calculations
                                if existing_trade.gross_pnl != gross_pnl or existing_trade.charges != charges:
                                    existing_trade.gross_pnl = gross_pnl
                                    existing_trade.charges = charges
                                    existing_trade.net_pnl = gross_pnl - charges
                                    needs_update = True
                                
                                # Update notes with latest ticket information
                                new_notes = f"MT5 position: {position_id}, entry ticket: {getattr(entry_deal, 'ticket', '')}, exit ticket: {getattr(exit_deal, 'ticket', '')}"
                                if existing_trade.notes != new_notes:
                                    existing_trade.notes = new_notes
                                    needs_update = True
                                
                                if needs_update:
                                    existing_trade.save()
                                    trades_updated += 1  # Count as updated
                            else:
                                # Create new trade
                                # Determine status based on whether position is closed
                                is_closed = len(deals) > 1 and exit_time > entry_time
                                trade_status = 'closed' if is_closed else 'open'
                                
                                Trade.objects.create(
                                    account=selected_account,
                                    instrument=instrument_name,
                                    entry_price=getattr(entry_deal, 'price', 0),
                                    exit_price=getattr(exit_deal, 'price', 0) if is_closed else None,
                                    entry_date=entry_time,
                                    exit_date=exit_time if is_closed else None,
                                    size=getattr(entry_deal, 'volume', 0),
                                    status=trade_status,
                                    notes=f"MT5 position: {position_id}, entry ticket: {getattr(entry_deal, 'ticket', '')}, exit ticket: {getattr(exit_deal, 'ticket', '')}",
                                    gross_pnl=gross_pnl,
                                    charges=charges,
                                    net_pnl=gross_pnl-charges
                                )
                                trades_fetched += 1
                            
                            # Track latest trade time
                            if not latest_trade_time or exit_time > latest_trade_time:
                                latest_trade_time = exit_time
                        
                        # Update last fetch timestamp
                        if latest_trade_time:
                            selected_account.mt5_last_fetch = latest_trade_time
                            selected_account.save()
                        
                        # Create descriptive message
                        message_parts = []
                        if trades_fetched > 0:
                            message_parts.append(f"{trades_fetched} new trade{'s' if trades_fetched != 1 else ''}")
                        if trades_updated > 0:
                            message_parts.append(f"{trades_updated} updated trade{'s' if trades_updated != 1 else ''}")
                        
                        if message_parts:
                            message = f"Fetched {' and '.join(message_parts)} from MT5 account '{selected_account.name}'."
                        else:
                            message = "No new or updated trades found in MT5."
                    mt5.shutdown()
    else:
        form = MT5FetchForm(user=request.user)


    
    return render(request, 'fetch_mt5_trades.html', {'form': form, 'message': message})

def fetch_mt5_trades_for_account(account):
    """Helper function to fetch trades for a specific MT5 account"""
    if not account.mt5_account_number or not account.mt5_server:
        raise ValueError("Account is not linked to MT5")
    
    if mt5 is None:
        raise ImportError("MetaTrader 5 library is not installed")
    
    # Note: This function assumes MT5 is already initialized and logged in
    # In a real implementation, you might want to store encrypted credentials
    # or require re-authentication for security
    
    # Get deals from the last 30 days
    from_date = datetime.now() - timedelta(days=30)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals is None:
        return 0
    
    imported_count = 0
    
    for deal in deals:
        # Skip if not a trade exit (entry = 0, exit = 1)
        if deal.entry != 1:
            continue
            
        # Check if trade already exists
        existing_trade = Trade.objects.filter(
            account=account,
            entry_date__date=datetime.fromtimestamp(deal.time).date(),
            instrument=deal.symbol,
            exit_price=deal.price
        ).first()
        
        if existing_trade:
            continue
        
        # Get corresponding entry deal
        entry_deals = mt5.history_deals_get(
            datetime.fromtimestamp(deal.time) - timedelta(days=7),
            datetime.fromtimestamp(deal.time),
            position=deal.position_id
        )
        
        entry_deal = None
        if entry_deals:
            for ed in entry_deals:
                if ed.entry == 0 and ed.position_id == deal.position_id:
                    entry_deal = ed
                    break
        
        if not entry_deal:
            continue
        
        # Create trade
        Trade.objects.create(
            account=account,
            instrument=deal.symbol,
            direction='long' if deal.type == 0 else 'short',
            status='closed',
            entry_price=entry_deal.price,
            exit_price=deal.price,
            entry_date=datetime.fromtimestamp(entry_deal.time),
            exit_date=datetime.fromtimestamp(deal.time),
            size=abs(deal.volume),
            gross_pnl=deal.profit,
            charges=deal.commission + deal.swap + deal.fee,
            net_pnl=deal.profit - (deal.commission + deal.swap + deal.fee)
        )
        
        imported_count += 1
    
    # Update last fetch time
    account.mt5_last_fetch = timezone.now()
    account.save()
    
    return imported_count

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TradeViewSet(viewsets.ModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Trade.objects.filter(account__user=self.request.user)
    def perform_create(self, serializer):
        serializer.save()

from .models import Trade
from django.shortcuts import get_object_or_404, render

def trade_detail_view(request, pk):
    trade = get_object_or_404(Trade, pk=pk)
    return render(request, 'trade_detail.html', {'trade': trade})

from django.http import HttpResponseForbidden

@login_required
def delete_trade_attachment(request, attachment_id):
    attachment = get_object_or_404(TradeAttachment, id=attachment_id)
    trade = attachment.trade
    if trade.account.user != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        attachment.delete()
        return redirect('trade_edit', pk=trade.pk)
    return render(request, 'trade_attachment_confirm_delete.html', {'attachment': attachment, 'trade': trade})

@login_required
def daily_checklist_view(request):
    import sys
    today = timezone.localdate()
    # Determine which date to show (from GET param or today)
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            selected_date = today
    else:
        selected_date = today

    # Find the latest template effective on or before selected_date
    template = DailyChecklistTemplate.objects.filter(effective_date__lte=selected_date).order_by('-effective_date').first()
    items = template.items.all() if template else []

    # For each item, get or create user progress for this date
    progress_map = {}
    is_holiday = False
    if request.user.is_authenticated:
        for item in items:
            progress, _ = UserDailyChecklistProgress.objects.get_or_create(
                user=request.user, item=item, date=selected_date,
                defaults={'checked': False}
            )
            progress_map[item.id] = progress
        # Check if any progress for this date is marked as holiday
        if items:
            is_holiday = UserDailyChecklistProgress.objects.filter(user=request.user, date=selected_date, holiday=True).exists()

    # Admin: handle template editing for future dates only
    is_admin = request.user.is_staff
    can_edit = is_admin and selected_date > today

    # Handle user check/uncheck (AJAX or POST)
    if request.method == 'POST' and not can_edit:
        # Debug: print POST data and progress_map before saving
        print(f"[DEBUG] POST data: {request.POST}", file=sys.stderr)
        print(f"[DEBUG] Progress map before saving:", file=sys.stderr)
        for k, v in progress_map.items():
            print(f"  Item {k}: checked={v.checked}", file=sys.stderr)
        holiday_val = request.POST.get('holiday')
        is_holiday = holiday_val == 'yes'
        for item in items:
            checked = request.POST.get(f'item_{item.id}') == 'on'
            progress = progress_map[item.id]
            progress.checked = checked
            progress.checked_at = timezone.now() if checked else None
            progress.holiday = is_holiday
            progress.save()
        # Debug: print progress_map after saving
        print(f"[DEBUG] Progress map after saving:", file=sys.stderr)
        for k, v in progress_map.items():
            print(f"  Item {k}: checked={v.checked}", file=sys.stderr)
        return redirect(f'{request.path}?date={selected_date}')

    if is_admin and request.method == 'POST' and can_edit:
        new_items = request.POST.getlist('admin_item')
        if new_items:
            new_template = DailyChecklistTemplate.objects.create(
                name=f'Admin {request.user.email} {selected_date}',
                effective_date=selected_date
            )
            for idx, text in enumerate(new_items):
                if text.strip():
                    DailyChecklistItem.objects.create(template=new_template, text=text, order=idx)
            return redirect(f'{request.path}?date={selected_date}')

    # After POST and redirect, re-fetch progress_map for GET
    if request.method == 'GET' and items:
        pass

    context = {
        'selected_date': selected_date,
        'template': template,
        'items': items,
        'progress_map': progress_map,
        'is_admin': is_admin,
        'can_edit': can_edit,
        'is_holiday': is_holiday,
    }
    return render(request, 'daily_checklist.html', context)

@login_required
def weekly_checklist_view(request):
    today = timezone.localdate()
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                selected_date = datetime.strptime(date_str, '%b %d, %Y').date()
            except Exception:
                selected_date = today
    else:
        selected_date = today
    # Find the start of the week (Monday)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    week = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        # Find checklist template for this day
        template = DailyChecklistTemplate.objects.filter(effective_date__lte=day).order_by('-effective_date').first()
        items = template.items.all() if template else []
        if items:
            progresses = UserDailyChecklistProgress.objects.filter(user=request.user, date=day, item__in=items)
            checked_count = progresses.filter(checked=True).count()
            is_holiday = progresses.filter(holiday=True).exists()
            percent = int(checked_count / items.count() * 100) if items.count() else 0
            percent = max(0, min(percent, 100))  # Clamp between 0 and 100
            percent_remaining = 100 - percent
            circumference = 125.66
            dashoffset = circumference * (1 - percent / 100)
            week.append({
                'date': day,
                'percent': percent,
                'percent_remaining': percent_remaining,
                'dashoffset': dashoffset,
                'has_checklist': True,
                'is_holiday': is_holiday,
                'bg_style': ''
            })
        else:
            week.append({
                'date': day,
                'percent': 0,
                'percent_remaining': 100,
                'dashoffset': 125.66,
                'has_checklist': False,
                'is_holiday': False,
                'bg_style': 'background: #ffb6c1;'
            })
    context = {
        'selected_date': selected_date,
        'week_days': week_days,
        'week': week,
    }
    return render(request, 'weekly_checklist.html', context)

@login_required
def monthly_checklist_view(request):
    today = timezone.localdate()
    month_str = request.GET.get('month')
    if month_str:
        year, month = map(int, month_str.split('-'))
        first_day = date(year, month, 1)
    else:
        first_day = today.replace(day=1)
        year, month = first_day.year, first_day.month
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cal = Calendar(firstweekday=0)
    month_grid = []
    for week in cal.monthdatescalendar(year, month):
        week_row = []
        for day in week:
            if day.month != month:
                week_row.append(None)
            else:
                template = DailyChecklistTemplate.objects.filter(effective_date__lte=day).order_by('-effective_date').first()
                items = template.items.all() if template else []
                if items:
                    progresses = UserDailyChecklistProgress.objects.filter(user=request.user, date=day, item__in=items)
                    checked_count = progresses.filter(checked=True).count()
                    is_holiday = progresses.filter(holiday=True).exists()
                    percent = int(checked_count / items.count() * 100) if items.count() else 0
                    percent = max(0, min(percent, 100))
                    percent_remaining = 100 - percent
                    circumference = 125.66
                    dashoffset = circumference * (1 - percent / 100)
                    week_row.append({
                        'date': day,
                        'percent': percent,
                        'percent_remaining': percent_remaining,
                        'dashoffset': dashoffset,
                        'has_checklist': True,
                        'is_holiday': is_holiday,
                        'bg_style': ''
                    })
                else:
                    week_row.append({
                        'date': day,
                        'percent': 0,
                        'percent_remaining': 100,
                        'dashoffset': 125.66,
                        'has_checklist': False,
                        'is_holiday': False,
                        'bg_style': 'background: #ffb6c1;'
                    })
        month_grid.append(week_row)
    context = {
        'selected_month': f"{year:04d}-{month:02d}",
        'week_days': week_days,
        'month_grid': month_grid,
        'today': today,
    }
    return render(request, 'monthly_checklist.html', context)

@login_required
def trade_plan_create_view(request):
    from .forms import TradePlanEventForm
    if request.method == 'POST':
        form = TradePlanForm(request.POST, request.FILES)
        event_form = TradePlanEventForm(request.POST, request.FILES)
        files = request.FILES.getlist('attachments')
        if form.is_valid() and event_form.is_valid():
            trade_plan = form.save(commit=False)
            trade_plan.user = request.user
            trade_plan.save()
            form.save_m2m()
            # Save attachments
            for f in files:
                TradePlanAttachment.objects.create(trade_plan=trade_plan, image=f)
            # Save initial event if any description is provided
            if event_form.cleaned_data.get('description'):
                event = event_form.save(commit=False)
                event.trade_plan = trade_plan
                event.save()
            return redirect('trade_plan_list')
    else:
        form = TradePlanForm()
        event_form = TradePlanEventForm()
    return render(request, 'trade_plan_form.html', {'form': form, 'event_form': event_form})

@login_required
def trade_plan_list_view(request):
    plans = TradePlan.objects.filter(user=request.user).order_by('-planned_at')
    status = request.GET.get('status')
    if status:
        plans = plans.filter(status=status)
    return render(request, 'trade_plan_list.html', {'plans': plans, 'status': status})

@login_required
def trade_plan_detail_view(request, pk):
    plan = get_object_or_404(TradePlan, pk=pk, user=request.user)
    return render(request, 'trade_plan_detail.html', {'plan': plan})

@login_required
def trade_plan_delete_view(request, pk):
    plan = get_object_or_404(TradePlan, pk=pk, user=request.user)
    if request.method == 'POST':
        plan.delete()
        return redirect('trade_plan_list')
    return render(request, 'trade_plan_confirm_delete.html', {'plan': plan})

@login_required
def trade_plan_event_add_view(request, plan_id):
    plan = get_object_or_404(TradePlan, pk=plan_id, user=request.user)
    from .forms import TradePlanEventForm
    if request.method == 'POST':
        form = TradePlanEventForm(request.POST, request.FILES)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            event = form.save(commit=False)
            event.trade_plan = plan
            event.save()
            # Save all uploaded files as attachments
            for f in files:
                TradePlanEventAttachment.objects.create(event=event, file=f)
            return redirect('trade_plan_detail', pk=plan.pk)
    else:
        form = TradePlanEventForm()
    return render(request, 'trade_plan_event_form.html', {'form': form, 'plan': plan})

@login_required
def trade_plan_event_edit_view(request, event_id):
    event = get_object_or_404(TradePlanEvent, pk=event_id, trade_plan__user=request.user)
    plan = event.trade_plan
    from .forms import TradePlanEventForm
    if request.method == 'POST':
        form = TradePlanEventForm(request.POST, request.FILES, instance=event)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            form.save()
            # Save new uploaded files as attachments
            for f in files:
                TradePlanEventAttachment.objects.create(event=event, file=f)
            return redirect('trade_plan_detail', pk=plan.pk)
    else:
        form = TradePlanEventForm(instance=event)
    return render(request, 'trade_plan_event_form.html', {'form': form, 'plan': plan, 'edit': True, 'event': event})

@login_required
def trade_plan_event_delete_view(request, event_id):
    event = get_object_or_404(TradePlanEvent, pk=event_id, trade_plan__user=request.user)
    plan = event.trade_plan
    if request.method == 'POST':
        event.delete()
        return redirect('trade_plan_detail', pk=plan.pk)
    return render(request, 'trade_plan_event_confirm_delete.html', {'event': event, 'plan': plan})

@login_required
def trade_plan_edit_view(request, pk):
    plan = get_object_or_404(TradePlan, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TradePlanForm(request.POST, request.FILES, instance=plan)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            plan = form.save()
            # Save new attachments
            for f in files:
                TradePlanAttachment.objects.create(trade_plan=plan, image=f)
            return redirect('trade_plan_detail', pk=plan.pk)
    else:
        form = TradePlanForm(instance=plan)
    return render(request, 'trade_plan_form.html', {'form': form, 'edit': True, 'plan': plan})

@login_required
def trade_plan_event_attachment_delete_view(request, attachment_id):
    att = get_object_or_404(TradePlanEventAttachment, pk=attachment_id, event__trade_plan__user=request.user)
    event = att.event
    plan = event.trade_plan
    if request.method == 'POST':
        att.delete()
        return redirect('trade_plan_event_edit', event_id=event.pk)
    return render(request, 'trade_attachment_confirm_delete.html', {'attachment': att, 'event': event, 'plan': plan, 'is_event_attachment': True})

@login_required
def milestone_list_view(request):
    milestones = Milestone.objects.all()
    return render(request, 'milestone_list.html', {'milestones': milestones})

@login_required
def milestone_create_view(request):
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('milestone_list')
    else:
        form = MilestoneForm()
    return render(request, 'milestone_form.html', {'form': form})

@login_required
def milestone_edit_view(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk)
    if request.method == 'POST':
        form = MilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            return redirect('milestone_list')
    else:
        form = MilestoneForm(instance=milestone)
    return render(request, 'milestone_form.html', {'form': form, 'edit': True})

@login_required
def milestone_delete_view(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk, user=request.user)
    if request.method == 'POST':
        milestone.delete()
        return redirect('milestone_list')
    return render(request, 'milestone_confirm_delete.html', {'milestone': milestone})

@login_required
def lesson_list_view(request):
    lessons = Lesson.objects.all()
    return render(request, 'lesson_list.html', {'lessons': lessons})

@login_required
def lesson_create_view(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')
    else:
        form = LessonForm()
    return render(request, 'lesson_form.html', {'form': form})

@login_required
def lesson_edit_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'lesson_form.html', {'form': form, 'edit': True})

@login_required
def lesson_delete_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    if request.method == 'POST':
        lesson.delete()
        return redirect('lesson_list')
    return render(request, 'lesson_confirm_delete.html', {'lesson': lesson})

@login_required
def achievement_list_view(request):
    achievements = Achievement.objects.all()
    return render(request, 'achievement_list.html', {'achievements': achievements})

@login_required
def achievement_create_view(request):
    if request.method == 'POST':
        form = AchievementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('achievement_list')
    else:
        form = AchievementForm()
    return render(request, 'achievement_form.html', {'form': form})

@login_required
def achievement_edit_view(request, pk):
    achievement = get_object_or_404(Achievement, pk=pk)
    if request.method == 'POST':
        form = AchievementForm(request.POST, instance=achievement)
        if form.is_valid():
            form.save()
            return redirect('achievement_list')
    else:
        form = AchievementForm(instance=achievement)
    return render(request, 'achievement_form.html', {'form': form, 'edit': True})

@login_required
def achievement_delete_view(request, pk):
    achievement = get_object_or_404(Achievement, pk=pk, user=request.user)
    if request.method == 'POST':
        achievement.delete()
        return redirect('achievement_list')
    return render(request, 'achievement_confirm_delete.html', {'achievement': achievement})

@login_required
def review_list_view(request):
    reviews = Review.objects.all()
    return render(request, 'review_list.html', {'reviews': reviews})

@login_required
def review_create_view(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('review_list')
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form})

@login_required
def review_edit_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'edit': True})

@login_required
def review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == 'POST':
        review.delete()
        return redirect('review_list')
    return render(request, 'review_confirm_delete.html', {'review': review})

@login_required
def course_list_view(request):
    courses = Course.objects.filter(user=request.user)
    return render(request, 'course_list.html', {'courses': courses})

@login_required
def course_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'course_form.html', {'form': form})

@login_required
def course_edit_view(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'course_form.html', {'form': form, 'edit': True})

@login_required
def course_delete_view(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request, 'course_confirm_delete.html', {'course': course})

@login_required
def book_list_view(request):
    books = Book.objects.filter(user=request.user)
    return render(request, 'book_list.html', {'books': books})

@login_required
def book_create_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'book_form.html', {'form': form})

@login_required
def book_edit_view(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'book_form.html', {'form': form, 'edit': True})

@login_required
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk, user=request.user)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'book_confirm_delete.html', {'book': book})

@login_required
def keylesson_list_view(request):
    keylessons = KeyLesson.objects.filter(user=request.user)
    return render(request, 'keylesson_list.html', {'keylessons': keylessons})

@login_required
def keylesson_create_view(request):
    if request.method == 'POST':
        form = KeyLessonForm(request.POST)
        if form.is_valid():
            keylesson = form.save(commit=False)
            keylesson.user = request.user
            keylesson.save()
            return redirect('keylesson_list')
    else:
        form = KeyLessonForm()
    return render(request, 'keylesson_form.html', {'form': form})

@login_required
def keylesson_edit_view(request, pk):
    keylesson = get_object_or_404(KeyLesson, pk=pk, user=request.user)
    if request.method == 'POST':
        form = KeyLessonForm(request.POST, instance=keylesson)
        if form.is_valid():
            form.save()
            return redirect('keylesson_list')
    else:
        form = KeyLessonForm(instance=keylesson)
    return render(request, 'keylesson_form.html', {'form': form, 'edit': True})

@login_required
def keylesson_delete_view(request, pk):
    keylesson = get_object_or_404(KeyLesson, pk=pk, user=request.user)
    if request.method == 'POST':
        keylesson.delete()
        return redirect('keylesson_list')
    return render(request, 'keylesson_confirm_delete.html', {'keylesson': keylesson})

@login_required
def mistake_list_view(request):
    mistakes = Mistake.objects.filter(user=request.user)
    return render(request, 'mistake_list.html', {'mistakes': mistakes})

@login_required
def mistake_create_view(request):
    if request.method == 'POST':
        form = MistakeForm(request.POST)
        if form.is_valid():
            mistake = form.save(commit=False)
            mistake.user = request.user
            mistake.save()
            return redirect('mistake_list')
    else:
        form = MistakeForm()
    return render(request, 'mistake_form.html', {'form': form})

@login_required
def mistake_edit_view(request, pk):
    mistake = get_object_or_404(Mistake, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MistakeForm(request.POST, instance=mistake)
        if form.is_valid():
            form.save()
            return redirect('mistake_list')
    else:
        form = MistakeForm(instance=mistake)
    return render(request, 'mistake_form.html', {'form': form, 'edit': True})

@login_required
def mistake_delete_view(request, pk):
    mistake = get_object_or_404(Mistake, pk=pk, user=request.user)
    if request.method == 'POST':
        mistake.delete()
        return redirect('mistake_list')
    return render(request, 'mistake_confirm_delete.html', {'mistake': mistake})

@login_required
def fetch_mt5_trades_view(request):
    """Fetch trades for the selected MT5 account"""
    selected_account_id = request.session.get('selected_account_id')
    
    if not selected_account_id:
        messages.error(request, 'No account selected.')
        return redirect('dashboard')
    
    try:
        account = Account.objects.get(id=selected_account_id, user=request.user)
        
        if not account.mt5_account_number:
            messages.error(request, 'Selected account is not linked to MT5.')
            return redirect('dashboard')
        
        # This would require re-authentication for security
        # For now, show a message that this feature needs MT5 credentials
        messages.info(request, 'MT5 trade refresh requires re-authentication. Please use the MT5 fetch tool.')
        return redirect('dashboard')
        
    except Account.DoesNotExist:
        messages.error(request, 'Account not found.')
        return redirect('dashboard')

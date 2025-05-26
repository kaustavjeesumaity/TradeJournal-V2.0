from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AccountForm, TradeForm, MT5FetchForm
from .forms_profile import ProfileForm
from .models import Account, Trade, TradeAttachment, Instrument
from django.urls import reverse
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.utils.dateparse import parse_date
import csv
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
    trades = Trade.objects.filter(account__user=request.user)

    # Filtering
    instrument = request.GET.get('instrument', '')
    outcome = request.GET.get('outcome', '')
    account_number = request.GET.get('account_number', '')
    start_date = request.GET.get('start_date', datetime.date.today().isoformat())
    end_date = request.GET.get('end_date', datetime.date.today().isoformat())
    sort = request.GET.get('sort', 'exit_date')

    if instrument:
        trades = trades.filter(instrument=instrument)
    if outcome == 'win':
        trades = trades.filter(exit_price__gt=F('entry_price'))
    elif outcome == 'loss':
        trades = trades.filter(exit_price__lt=F('entry_price'))
    if account_number:
        try:
            account_number_int = int(account_number)
            trades = trades.filter(account__pk=account_number_int)
        except ValueError:
            # Ignore filter if account_number is not an integer (e.g., legacy or invalid value)
            pass
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
        account_pnl = sum([t.pnl for t in account_trades])
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
    total_pnl = sum([t.pnl for t in trades])
    total_trades = trades.count()
    wins = trades.filter(exit_price__gt=F('entry_price')).count()
    losses = trades.filter(exit_price__lt=F('entry_price')).count()
    win_rate = (wins / total_trades * 100) if total_trades else 0
    avg_risk_reward = (
        sum([(t.exit_price - t.entry_price) / abs(t.entry_price) for t in trades if t.entry_price != 0]) / total_trades
        if total_trades else 0
    )
    # PnL trend data for chart
    pnl_dates = [t.exit_date.strftime('%Y-%m-%d') for t in trades.order_by('exit_date')]
    pnl_values = [float(t.pnl) for t in trades.order_by('exit_date')]

    # Instrument analytics
    instrument_stats = []
    instrument_map = defaultdict(list)
    for t in trades:
        instrument_map[t.instrument].append(t)
    for instrument, tlist in instrument_map.items():
        count = len(tlist)
        wins = len([t for t in tlist if t.exit_price > t.entry_price])
        pnl = sum([t.pnl for t in tlist])
        win_rate = (wins / count * 100) if count else 0
        instrument_stats.append({
            'instrument': instrument,
            'count': count,
            'win_rate': win_rate,
            'pnl': pnl,
        })

    # Outcome analytics
    outcome_stats = []
    for outcome_label, filter_func in [
        ("Win", lambda t: t.exit_price > t.entry_price),
        ("Loss", lambda t: t.exit_price < t.entry_price),
        ("Break-even", lambda t: t.exit_price == t.entry_price),
    ]:
        tlist = [t for t in trades if filter_func(t)]
        count = len(tlist)
        wins = len([t for t in tlist if t.exit_price > t.entry_price])
        pnl = sum([t.pnl for t in tlist])
        win_rate = (wins / count * 100) if count else 0
        outcome_stats.append({
            'outcome': outcome_label,
            'count': count,
            'win_rate': win_rate,
            'pnl': pnl,
        })

    # For filter dropdowns
    instrument_list = list(Instrument.objects.values_list('name', flat=True).order_by('name'))
    # Show all account names in the dropdown, but use account.pk as the value for filtering
    account_options = [(account.pk, account.name) for account in accounts]
    default_account = account_options[0][0] if account_options else ''

    return render(request, 'dashboard.html', {
        'accounts': accounts,
        'account_summaries': account_summaries,
        'trades': page_obj.object_list if 'page_obj' in locals() else trades,
        'page_obj': page_obj if 'page_obj' in locals() else None,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'avg_risk_reward': avg_risk_reward,
        'pnl_dates': pnl_dates,
        'pnl_values': pnl_values,
        'filter': {
            'instrument': instrument,
            'outcome': outcome,
            'account_number': account_number,
            'start_date': start_date,
            'end_date': end_date,
            'sort': sort,
        },
        'base_currency': base_currency,
        'conversion_rates': conversion_rates,
        'instrument_stats': instrument_stats,
        'outcome_stats': outcome_stats,
        'instrument_list': instrument_list,
        'account_options': account_options,
        'default_account': default_account,
    })

@login_required
def account_create_view(request):
    # Prevent manual creation of MT5-linked accounts
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            # If user tries to submit MT5 fields, block it
            if form.cleaned_data.get('mt5_account_number') or form.cleaned_data.get('mt5_server'):
                form.add_error(None, 'Manual creation of MT5-linked accounts is not allowed. Use the MT5 fetch tool.')
            else:
                account = form.save(commit=False)
                account.user = request.user
                account.save()
                return redirect('dashboard')
    else:
        form = AccountForm()
    return render(request, 'account_form.html', {'form': form})

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
                # Handle attachment
                attachment = form.cleaned_data.get('attachment')
                if attachment:
                    TradeAttachment.objects.create(trade=trade, file=attachment)
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
        if form.is_valid():
            trade = form.save(commit=False)
            # Calculate net_pnl if gross_pnl and charges are provided
            gross_pnl = form.cleaned_data.get('gross_pnl')
            charges = form.cleaned_data.get('charges')
            if gross_pnl is not None and charges is not None:
                trade.gross_pnl = gross_pnl
                trade.charges = charges
                trade.net_pnl = gross_pnl - charges
            trade.save()
            form.save_m2m()
            # Handle new attachment
            attachment = form.cleaned_data.get('attachment')
            if attachment:
                TradeAttachment.objects.create(trade=trade, file=attachment)
            return redirect('dashboard')
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
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

@login_required
def trade_export_csv(request):
    trades = Trade.objects.filter(account__user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trades.csv"'
    writer = csv.writer(response)
    writer.writerow(['account', 'instrument', 'entry_price', 'exit_price', 'entry_date', 'exit_date', 'quantity', 'notes'])
    for t in trades:
        writer.writerow([
            t.account.name,
            t.instrument,
            t.entry_price,
            t.exit_price,
            t.entry_date,
            t.exit_date,
            t.quantity,
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
                quantity=row['quantity'],
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
    if request.method == 'POST':
        form = MT5FetchForm(request.POST)
        if form.is_valid():
            mt5_account = form.cleaned_data['mt5_account']
            mt5_server = form.cleaned_data['mt5_server']
            mt5_password = form.cleaned_data['mt5_password']
            if not mt5:
                message = 'MetaTrader5 package is not installed.'
            else:
                # Find or create the Account for this user+mt5_account+mt5_server
                account, created = Account.objects.get_or_create(
                    user=request.user,
                    mt5_account_number=mt5_account,
                    mt5_server=mt5_server,
                    defaults={
                        'name': f"MT5 {mt5_account} @ {mt5_server}",
                        'balance': 0,
                        'currency': 'USD',
                    }
                )
                # Initialize MT5
                if not mt5.initialize(server=mt5_server, login=int(mt5_account), password=mt5_password):
                    message = f"MT5 initialize() failed: {mt5.last_error()}"
                else:
                    # Fetch only trades after last fetch
                    from datetime import datetime, timezone
                    last_fetch = account.mt5_last_fetch
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
                            if Trade.objects.filter(account=account, notes__contains=f"MT5 position: {position_id}").exists():
                                continue
                            # Add instrument to Instrument model if not exists
                            instrument_name = getattr(entry_deal, 'symbol', '')
                            if instrument_name and not Instrument.objects.filter(name=instrument_name).exists():
                                Instrument.objects.create(name=instrument_name)
                            Trade.objects.create(
                                account=account,
                                instrument=instrument_name,
                                entry_price=getattr(entry_deal, 'price', 0),
                                exit_price=getattr(exit_deal, 'price', 0),
                                entry_date=entry_time,
                                exit_date=exit_time,
                                quantity=getattr(entry_deal, 'volume', 0),
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
                            account.mt5_last_fetch = latest_trade_time
                            account.save()
                        message = f"Fetched {trades_fetched} new trades from MT5."
                    mt5.shutdown()
    else:
        form = MT5FetchForm()
    return render(request, 'fetch_mt5_trades.html', {'form': form, 'message': message})

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

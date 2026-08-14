from datetime import date
from decimal import Decimal
from functools import wraps
import secrets
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.utils import transliterate_ro
from menu.models import Favorite
from reservations.models import Reservation
from .forms import TicketForm, WaitlistForm
from .models import Event, Expense, Invoice, LoyaltyAccount, LoyaltyRedemption, LoyaltyTransaction, Sale, StaffProfile, StaffShift, StockItem, Ticket


def _line_total(price_field, quantity_field='quantity'):
    return ExpressionWrapper(F(price_field) * F(quantity_field), output_field=DecimalField(max_digits=12, decimal_places=2))


def _expenses_by_category(queryset):
    """Single-query breakdown of an Expense queryset by category, in Expense.CATEGORIES order."""
    totals = {row['category']: row['total'] for row in queryset.values('category').annotate(total=Sum('amount'))}
    return [(label, totals.get(code) or Decimal('0')) for code, label in Expense.CATEGORIES]


def manager_required(view_func):
    """Restricts a view to CEO/Manager staff (or superusers) — financial data
    shouldn't be visible to every is_staff account regardless of StaffProfile.role."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, 'staff_profile', None)
        allowed_roles = (StaffProfile.CEO, StaffProfile.MANAGER)
        if not (request.user.is_superuser or (profile and profile.role in allowed_roles)):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def events(request):
    return render(request, 'operations/events.html', {
        'upcoming_events': Event.objects.filter(is_active=True, starts_at__gte=timezone.now()).order_by('starts_at'),
        'past_events': Event.objects.filter(is_active=True, starts_at__lt=timezone.now()).order_by('-starts_at'),
    })


def waitlist(request):
    form = WaitlistForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'You have been added to the waitlist. We will contact you if a table becomes available.')
        return redirect('operations:waitlist')
    return render(request, 'operations/waitlist.html', {'form': form})


def event_booking(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)
    if (event.ends_at or event.starts_at) < timezone.now():
        messages.error(request, 'This event has already taken place.')
        return redirect('operations:events')
    form = TicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quantity = form.cleaned_data['quantity']
        with transaction.atomic():
            locked_event = Event.objects.select_for_update().get(pk=event.pk)
            if locked_event.capacity:
                booked = Ticket.objects.filter(event=locked_event).aggregate(total=Sum('quantity'))['total'] or 0
                remaining = locked_event.capacity - booked
                if quantity > remaining:
                    form.add_error('quantity', f'Only {max(remaining, 0)} spots left for this event.')
                    return render(request, 'operations/event_booking.html', {'event': event, 'form': form})
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.paid = event.is_free
            ticket.save()
        messages.success(request, 'Your event registration has been recorded.' if event.is_free else 'Your ticket has been reserved. Our team will contact you to arrange payment.')
        return redirect('operations:events')
    return render(request, 'operations/event_booking.html', {'event': event, 'form': form})


@login_required
def client_dashboard(request):
    account, _ = LoyaltyAccount.objects.get_or_create(user=request.user)
    points = account.points
    progress_percent = 100 if (points > 0 and points % 100 == 0) else points % 100
    return render(request, 'operations/client_dashboard.html', {
        'reservations': Reservation.objects.filter(user=request.user).select_related('table').order_by('-reservation_date'),
        'loyalty_account': account,
        'redemptions': account.redemptions.select_related('reward').all()[:5],
        'today': timezone.localdate(),
        'loyalty_progress_percent': progress_percent,
        'favorite_items': Favorite.objects.filter(user=request.user).select_related('item', 'item__category'),
    })


@login_required
def redeem_reward(request):
    if request.method != 'POST':
        return redirect('operations:client_dashboard')
    account, _ = LoyaltyAccount.objects.get_or_create(user=request.user)
    from menu.models import MenuItem
    dessert = MenuItem.objects.filter(is_loyalty_reward=True, is_available=True).first()
    if account.points < 100:
        messages.error(request, 'You need at least 100 points to claim this reward.')
        return redirect('operations:client_dashboard')
    if not dessert:
        messages.error(request, 'No eligible dessert is available for this reward right now.')
        return redirect('operations:client_dashboard')
    with transaction.atomic():
        account = LoyaltyAccount.objects.select_for_update().get(pk=account.pk)
        if account.points < 100:
            messages.error(request, 'Your points have changed. You can no longer claim this reward.')
            return redirect('operations:client_dashboard')
        account.points -= 100
        account.save(update_fields=('points', 'updated_at'))
        LoyaltyTransaction.objects.create(account=account, points=-100, note='Reward: free dessert')
        code = f'DESERT-{secrets.token_hex(4).upper()}'
        LoyaltyRedemption.objects.create(account=account, code=code, reward=dessert)
    messages.success(request, f'Your reward is ready: {code}. Show this code to staff to redeem your {dessert.name}.')
    return redirect('operations:client_dashboard')


@staff_member_required
@manager_required
def staff_dashboard(request):
    sales_total = Sale.objects.aggregate(total=Sum(_line_total('unit_price')))['total'] or Decimal('0')
    advance_total = Reservation.objects.filter(advance_paid=True).aggregate(total=Sum('advance_amount'))['total'] or Decimal('0')
    ticket_total = Ticket.objects.filter(paid=True).aggregate(total=Sum(_line_total('event__ticket_price')))['total'] or Decimal('0')
    paid_expenses = Expense.objects.filter(paid=True)
    expenses_total = paid_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expense_by_category = _expenses_by_category(paid_expenses)
    return render(request, 'operations/staff_dashboard.html', {'sales_total': sales_total, 'advance_total': advance_total, 'ticket_total': ticket_total, 'expenses_total': expenses_total, 'expense_by_category': expense_by_category, 'profit': sales_total + advance_total + ticket_total - expenses_total, 'low_stock': StockItem.objects.filter(quantity__lt=F('minimum_quantity')), 'expired_stock': StockItem.objects.filter(expiry_date__lt=timezone.localdate()), 'pending_reservations': Reservation.objects.filter(status='pending').count(), 'invoices': Invoice.objects.all()[:5]})


@staff_member_required
@manager_required
def reports(request):
    today = timezone.localdate()

    def parse_date(value, default):
        try:
            return date.fromisoformat(value) if value else default
        except ValueError:
            return default

    start = parse_date(request.GET.get('start'), today.replace(day=1))
    end = parse_date(request.GET.get('end'), today)
    start, end = (start, end) if start <= end else (end, start)

    sales = Sale.objects.filter(created_at__date__range=(start, end))
    tickets = Ticket.objects.filter(paid=True, created_at__date__range=(start, end))
    advances = Reservation.objects.filter(advance_paid=True, created_at__date__range=(start, end))
    expenses = Expense.objects.filter(expense_date__range=(start, end), paid=True)

    sales_revenue = sales.aggregate(total=Sum(_line_total('unit_price')))['total'] or Decimal('0')
    ticket_revenue = tickets.aggregate(total=Sum(_line_total('event__ticket_price')))['total'] or Decimal('0')
    advance_revenue = advances.aggregate(total=Sum('advance_amount'))['total'] or Decimal('0')
    revenue = sales_revenue + ticket_revenue + advance_revenue

    expense_by_category = _expenses_by_category(expenses)
    expense_total = sum((total for _, total in expense_by_category), Decimal('0'))

    daily_sales = sales.annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum(_line_total('unit_price'))).order_by('day')
    top_items = sales.values('menu_item_id', 'menu_item__name').annotate(total_quantity=Sum('quantity'), revenue=Sum(_line_total('unit_price'))).order_by('-total_quantity')[:10]

    return render(request, 'operations/reports.html', {
        'start': start, 'end': end,
        'sales_revenue': sales_revenue, 'ticket_revenue': ticket_revenue, 'advance_revenue': advance_revenue,
        'revenue': revenue,
        'expense_by_category': expense_by_category, 'expenses': expense_total,
        'profit': revenue - expense_total,
        'daily_sales': daily_sales, 'top_items': top_items,
    })


@staff_member_required
def staff_schedule(request):
    return render(request, 'operations/staff_schedule.html', {'shifts': StaffShift.objects.select_related('staff__user').filter(ends_at__gte=timezone.now()).order_by('starts_at'), 'staff': StaffProfile.objects.select_related('user')})


@staff_member_required
@manager_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    # Minimal, dependency-free PDF document. Billing details are entered by staff
    # in Admin and the endpoint serves a downloadable/printable invoice.
    lines = [
        transliterate_ro(line) for line in [
            'AL NOIR - INVOICE', f'Number: {invoice.number}', f'Date: {invoice.issued_at:%d.%m.%Y}',
            f'Client: {invoice.customer_name}', f'Description: {invoice.description}',
            f'Total: ${invoice.amount:.2f}', 'Status: PAID' if invoice.paid else 'Status: UNPAID',
        ]
    ]
    def esc(value): return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    content = 'BT /F1 12 Tf 72 760 Td ' + ' 0 -22 Td '.join(f'({esc(line)}) Tj' for line in lines) + ' ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>', b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>', f'<< /Length {len(content.encode("latin-1", "replace"))} >>\nstream\n{content}\nendstream'.encode('latin-1', 'replace'), b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    pdf, offsets = bytearray(b'%PDF-1.4\n'), []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf)); pdf.extend(f'{index} 0 obj\n'.encode()); pdf.extend(obj); pdf.extend(b'\nendobj\n')
    start = len(pdf); pdf.extend(f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode())
    for offset in offsets: pdf.extend(f'{offset:010d} 00000 n \n'.encode())
    pdf.extend(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode())
    response = HttpResponse(bytes(pdf), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice-{invoice.number}.pdf"'
    return response

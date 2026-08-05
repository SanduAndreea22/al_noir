from datetime import date
from decimal import Decimal
import secrets
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.utils import transliterate_ro
from reservations.models import Reservation
from .forms import TicketForm, WaitlistForm
from .models import Event, Expense, Invoice, LoyaltyAccount, LoyaltyRedemption, LoyaltyTransaction, Sale, StaffProfile, StaffShift, StockItem, Ticket


def events(request):
    return render(request, 'operations/events.html', {'events': Event.objects.filter(is_active=True, starts_at__gte=timezone.now())})


def waitlist(request):
    form = WaitlistForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ai fost adăugat(ă) pe lista de așteptare. Te contactăm dacă se eliberează o masă.')
        return redirect('operations:waitlist')
    return render(request, 'operations/waitlist.html', {'form': form})


def event_booking(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)
    form = TicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quantity = form.cleaned_data['quantity']
        with transaction.atomic():
            locked_event = Event.objects.select_for_update().get(pk=event.pk)
            if locked_event.capacity:
                booked = Ticket.objects.filter(event=locked_event).aggregate(total=Sum('quantity'))['total'] or 0
                remaining = locked_event.capacity - booked
                if quantity > remaining:
                    form.add_error('quantity', f'Mai sunt doar {max(remaining, 0)} locuri disponibile la acest eveniment.')
                    return render(request, 'operations/event_booking.html', {'event': event, 'form': form})
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.paid = event.is_free
            ticket.save()
        messages.success(request, 'Rezervarea pentru eveniment a fost înregistrată.' if event.is_free else 'Biletul a fost rezervat. Configurează Stripe pentru plata online.')
        return redirect('operations:events')
    return render(request, 'operations/event_booking.html', {'event': event, 'form': form})


@login_required
def client_dashboard(request):
    account, _ = LoyaltyAccount.objects.get_or_create(user=request.user)
    return render(request, 'operations/client_dashboard.html', {
        'reservations': Reservation.objects.filter(user=request.user).order_by('-reservation_date'),
        'loyalty_account': account,
        'redemptions': account.redemptions.select_related('reward').all()[:5],
    })


@login_required
def redeem_reward(request):
    if request.method != 'POST':
        return redirect('operations:client_dashboard')
    account, _ = LoyaltyAccount.objects.get_or_create(user=request.user)
    from menu.models import MenuItem
    dessert = MenuItem.objects.filter(is_loyalty_reward=True, is_available=True).first()
    if account.points < 100 or not dessert:
        messages.error(request, 'Nu există suficiente puncte sau niciun desert eligibil disponibil.')
        return redirect('operations:client_dashboard')
    with transaction.atomic():
        account = LoyaltyAccount.objects.select_for_update().get(pk=account.pk)
        if account.points < 100:
            messages.error(request, 'Punctele au fost actualizate. Nu mai poți solicita recompensa.')
            return redirect('operations:client_dashboard')
        account.points -= 100
        account.save(update_fields=('points', 'updated_at'))
        LoyaltyTransaction.objects.create(account=account, points=-100, note='Recompensă: desert gratuit')
        code = f'DESERT-{secrets.token_hex(4).upper()}'
        LoyaltyRedemption.objects.create(account=account, code=code, reward=dessert)
    messages.success(request, f'Recompensa ta este gata: {code}. Arată acest cod personalului pentru {dessert.name}.')
    return redirect('operations:client_dashboard')


@staff_member_required
def staff_dashboard(request):
    sales_total = Sale.objects.aggregate(total=Sum(ExpressionWrapper(F('unit_price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))))['total'] or Decimal('0')
    advance_total = Reservation.objects.filter(advance_paid=True).aggregate(total=Sum('advance_amount'))['total'] or Decimal('0')
    ticket_total = Ticket.objects.filter(paid=True).aggregate(total=Sum(ExpressionWrapper(F('event__ticket_price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))))['total'] or Decimal('0')
    expenses_total = Expense.objects.filter(paid=True).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'operations/staff_dashboard.html', {'sales_total': sales_total, 'advance_total': advance_total, 'ticket_total': ticket_total, 'expenses_total': expenses_total, 'profit': sales_total + advance_total + ticket_total - expenses_total, 'low_stock': StockItem.objects.filter(quantity__lt=F('minimum_quantity')), 'expired_stock': StockItem.objects.filter(expiry_date__lt=timezone.localdate()), 'pending_reservations': Reservation.objects.filter(status='pending').count(), 'invoices': Invoice.objects.all()[:5]})


@staff_member_required
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
    expenses = Expense.objects.filter(expense_date__range=(start, end), paid=True)
    revenue = sales.aggregate(total=Sum(ExpressionWrapper(F('unit_price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))))['total'] or Decimal('0')
    expense_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    daily_sales = sales.annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum(ExpressionWrapper(F('unit_price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2)))).order_by('day')
    top_items = sales.values('menu_item__name').annotate(total_quantity=Sum('quantity'), revenue=Sum(ExpressionWrapper(F('unit_price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2)))).order_by('-total_quantity')[:10]
    return render(request, 'operations/reports.html', {'start': start, 'end': end, 'revenue': revenue, 'expenses': expense_total, 'profit': revenue - expense_total, 'daily_sales': daily_sales, 'top_items': top_items})


@staff_member_required
def staff_schedule(request):
    return render(request, 'operations/staff_schedule.html', {'shifts': StaffShift.objects.select_related('staff__user').filter(ends_at__gte=timezone.now()).order_by('starts_at'), 'staff': StaffProfile.objects.select_related('user')})


@staff_member_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    # Minimal, dependency-free PDF document. Billing details are entered by staff
    # in Admin and the endpoint serves a downloadable/printable invoice.
    lines = [
        transliterate_ro(line) for line in [
            'AL NOIR - FACTURA', f'Numar: {invoice.number}', f'Data: {invoice.issued_at:%d.%m.%Y}',
            f'Client: {invoice.customer_name}', f'Descriere: {invoice.description}',
            f'Total: {invoice.amount:.2f} RON', 'Status: ACHITATA' if invoice.paid else 'Status: NEACHITATA',
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
    response['Content-Disposition'] = f'attachment; filename="factura-{invoice.number}.pdf"'
    return response

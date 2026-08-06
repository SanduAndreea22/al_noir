import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import Review
from menu.models import MenuItem
from operations.models import (
    Event, Expense, LoyaltyRedemption, LoyaltyTransaction,
    Sale, StockItem, StockMovement, Ticket,
)
from reservations.models import Reservation, Table

MARKER_NAME = 'Demo Seed Marker'

REVIEWS = [
    ("Andreea M.", "Every dish felt carefully thought out — the tagliatelle with beef and wild mushrooms was outstanding. Will be back with the whole family.", 5),
    ("James Whitfield", "Found this place on a work trip to Bucharest and it completely exceeded expectations. Warm service, beautiful room.", 5),
    ("Sofia Marinescu", "Lovely evening, great wine pairing suggestions from the staff. A bit loud on a Saturday but the food made up for it.", 4),
    ("Michael Chen", "Best bruschetta I've had outside of Italy, honestly. Basil was clearly fresh, not from a jar.", 5),
    ("Elena Dobre", "We celebrated our anniversary here. The staff arranged a small surprise dessert without us asking twice. Very touched.", 5),
    ("Thomas Berger", "Solid food, good portions. Service was a little slow when it got busy around 8pm, but nobody rushed us either.", 4),
    ("Ioana Radu", "Went for the Sunday brunch, will definitely come again. Great value for the quality.", 5),
    ("David Cohen", "Reserved a table for 6 and everything was ready exactly on time. Loved the grilled dishes especially.", 5),
    ("Maria Ionescu", "Nice ambiance but I had to ask twice for the bill. Food was good though, no complaints there.", 3),
    ("Lucas Fischer", "The baklava dessert alone is worth the visit. Rich but not overly sweet.", 5),
    ("Alexandra Popa", "Cozy spot, friendly staff, and the loyalty program is a nice touch for regulars like us.", 4),
    ("Robert Klein", "Booked online, easy process, table was ready. Steak was cooked exactly as requested.", 5),
    ("Diana Stanciu", "Good experience overall. Wine list could use a couple more affordable options, but the food justified the price.", 4),
    ("Omar Al-Farsi", "Wonderful evening with friends. The staff recommended dishes based on what we liked and every suggestion landed.", 5),
]

CUSTOMER_NAMES = [
    ("Ana", "Georgescu"), ("Bogdan", "Enache"), ("Claudia", "Vasilescu"),
    ("Vlad", "Constantin"), ("Simona", "Barbu"), ("George", "Munteanu"),
]

RESERVATION_NAMES = [
    ("Cristina Neagu", "+40 745 112 998"), ("Paul Anderson", "+44 7700 900321"),
    ("Raluca Iliescu", "+40 722 384 771"), ("Hans Zimmermann", "+49 151 23456789"),
    ("Bianca Toma", "+40 731 552 019"), ("Sarah Johnson", "+1 415 555 0132"),
    ("Mihai Stoica", "+40 762 908 441"), ("Isabelle Laurent", "+33 6 12 34 56 78"),
    ("Andrei Pavel", "+40 748 220 634"), ("Emma Wilson", "+44 7911 123456"),
    ("Georgiana Sava", "+40 723 771 205"), ("Marco Rossi", "+39 333 1234567"),
    ("Florin Dumitrescu", "+40 755 903 118"), ("Nadia Petrescu", "+40 740 662 887"),
]

SPECIAL_REQUESTS = [
    '', '', '', 'Window table if possible.', 'Celebrating a birthday, could you bring a candle?',
    'One guest has a nut allergy.', 'Quiet table for a business dinner, please.',
    'Celebrating our anniversary.', 'High chair needed for a toddler.',
]

MENU_TIMES = [time(13, 0), time(13, 30), time(14, 0), time(19, 0), time(19, 30), time(20, 0), time(20, 30), time(21, 0)]


class Command(BaseCommand):
    help = (
        'Populates the database with realistic-looking demo content (reviews, '
        'reservation history, sales, expenses, events/tickets, loyalty customers). '
        'Idempotent — runs once and is safe to include in every deploy.'
    )

    def handle(self, *args, **options):
        if Review.objects.filter(name=MARKER_NAME).exists():
            self.stdout.write('Demo data already seeded, skipping.')
            return

        self.now = timezone.now()
        self.today = timezone.localdate()
        random.seed(42)

        with transaction.atomic():
            self.seed_reviews()
            customers = self.seed_customers()
            menu_items = list(MenuItem.objects.filter(is_available=True))
            tables = list(Table.objects.filter(status='available'))
            self.replenish_stock()
            self.seed_reservations(tables, menu_items, customers)
            self.seed_sales(menu_items, customers)
            self.seed_expenses()
            self.seed_events()
            Review.objects.create(name=MARKER_NAME, review_text='Internal marker, do not display.', rating=5, is_approved=False)

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete.'))

    def backdate(self, queryset, pk, when):
        queryset.filter(pk=pk).update(created_at=when)

    def business_datetime(self, day, clock_time=None):
        clock_time = clock_time or random.choice(MENU_TIMES)
        return timezone.make_aware(datetime.combine(day, clock_time))

    # ---- reviews -----------------------------------------------------
    def seed_reviews(self):
        for i, (name, text, rating) in enumerate(REVIEWS):
            offset = random.randint(2, 95)
            approved = not (i >= len(REVIEWS) - 2 and offset < 5)
            review = Review.objects.create(
                name=name,
                email=f"{name.split()[0].lower()}.{random.randint(10, 99)}@example.com",
                review_text=text,
                rating=rating,
                is_approved=approved,
            )
            self.backdate(Review.objects, review.pk, self.now - timedelta(days=offset, hours=random.randint(0, 12)))
        self.stdout.write(f'Created {len(REVIEWS)} reviews.')

    # ---- customers -----------------------------------------------------
    def seed_customers(self):
        customers = []
        for first, last in CUSTOMER_NAMES:
            username = f"{first.lower()}.{last.lower()}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first, 'last_name': last,
                    'email': f"{username}@example.com",
                    'is_staff': False, 'is_active': True,
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            customers.append(user)
        self.stdout.write(f'Created/verified {len(customers)} customer accounts.')
        return customers

    # ---- stock -----------------------------------------------------
    def replenish_stock(self):
        items = StockItem.objects.filter(menu_items__isnull=False).distinct()
        for item in items:
            if item.quantity < item.minimum_quantity * 3:
                topup = item.minimum_quantity * 10 or Decimal('50')
                movement = StockMovement.objects.create(
                    item=item, movement_type=StockMovement.PURCHASE,
                    quantity=topup, note='Demo seed: supplier restock',
                )
                self.backdate(StockMovement.objects, movement.pk, self.now - timedelta(days=88))

    # ---- reservations -----------------------------------------------------
    def seed_reservations(self, tables, menu_items, customers):
        if not tables:
            self.stdout.write('No tables found, skipping reservations.')
            return

        taken_slots = set(
            Reservation.objects.filter(status__in=['pending', 'confirmed'])
            .values_list('table_id', 'reservation_date', 'reservation_time')
        )

        def free_slot(day_choices):
            random.shuffle(tables)
            for table in tables:
                days = list(day_choices)
                random.shuffle(days)
                for day in days:
                    times = list(MENU_TIMES)
                    random.shuffle(times)
                    for t in times:
                        key = (table.id, day, t)
                        if key not in taken_slots:
                            taken_slots.add(key)
                            return table, day, t
            return None

        def guests_for(capacity):
            low = 1 if capacity <= 2 else max(2, capacity - 3)
            return random.randint(low, capacity)

        past_days = [self.today - timedelta(days=d) for d in range(1, 76)]
        future_days = [self.today + timedelta(days=d) for d in range(1, 22)]

        created_count = 0
        for _ in range(26):
            slot = free_slot(past_days)
            if not slot:
                break
            table, day, t = slot
            name, phone = random.choice(RESERVATION_NAMES)
            status = 'confirmed' if random.random() < 0.82 else 'cancelled'
            with_deposit = status == 'confirmed' and random.random() < 0.5 and menu_items
            reservation = Reservation(
                table=table, name=name, phone=phone,
                email=f"{name.split()[0].lower()}@example.com",
                reservation_date=day, reservation_time=t,
                guests=guests_for(table.capacity),
                special_request=random.choice(SPECIAL_REQUESTS),
                status=status,
                user=random.choice(customers) if random.random() < 0.3 else None,
            )
            reservation.save()
            if with_deposit:
                picks = random.sample(menu_items, k=min(len(menu_items), random.randint(2, 4)))
                reservation.selected_items.set(picks)
                subtotal = sum((item.price for item in picks), start=Decimal('0'))
                reservation.advance_amount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                reservation.advance_paid = True
                reservation.save(update_fields=['advance_amount', 'advance_paid'])
            when = self.business_datetime(day - timedelta(days=random.randint(2, 9)), t)
            self.backdate(Reservation.objects, reservation.pk, when)
            created_count += 1

        for _ in range(11):
            slot = free_slot(future_days)
            if not slot:
                break
            table, day, t = slot
            name, phone = random.choice(RESERVATION_NAMES)
            with_deposit = random.random() < 0.4 and menu_items
            status = 'confirmed' if with_deposit or random.random() < 0.6 else 'pending'
            reservation = Reservation(
                table=table, name=name, phone=phone,
                email=f"{name.split()[0].lower()}@example.com",
                reservation_date=day, reservation_time=t,
                guests=guests_for(table.capacity),
                special_request=random.choice(SPECIAL_REQUESTS),
                status=status,
                user=random.choice(customers) if random.random() < 0.3 else None,
            )
            reservation.save()
            if with_deposit:
                picks = random.sample(menu_items, k=min(len(menu_items), random.randint(2, 4)))
                reservation.selected_items.set(picks)
                subtotal = sum((item.price for item in picks), start=Decimal('0'))
                reservation.advance_amount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
                reservation.advance_paid = True
                reservation.save(update_fields=['advance_amount', 'advance_paid'])
            when = self.now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 10))
            self.backdate(Reservation.objects, reservation.pk, when)
            created_count += 1

        self.stdout.write(f'Created {created_count} reservations.')

    # ---- sales -----------------------------------------------------
    def seed_sales(self, menu_items, customers):
        if not menu_items:
            self.stdout.write('No available menu items, skipping sales.')
            return

        count = 0
        for d in range(0, 90):
            day = self.today - timedelta(days=d)
            weekday = day.weekday()
            base = 6 if weekday in (4, 5) else 3
            for _ in range(random.randint(max(0, base - 2), base + 3)):
                item = random.choice(menu_items)
                customer = random.choice(customers) if random.random() < 0.3 else None
                sale = Sale.objects.create(
                    menu_item=item,
                    customer=customer,
                    quantity=random.randint(1, 3),
                    unit_price=item.price,
                    payment_method=random.choices(['card', 'cash', 'online'], weights=[55, 30, 15])[0],
                )
                when = self.business_datetime(day)
                self.backdate(Sale.objects, sale.pk, when)
                if sale.stock_item_id:
                    StockMovement.objects.filter(item_id=sale.stock_item_id, note=f'Sale #{sale.pk}').update(created_at=when)
                if customer:
                    LoyaltyTransaction.objects.filter(account__user=customer, note=f'Sale #{sale.pk}').update(created_at=when)
                count += 1
        self.stdout.write(f'Created {count} sales.')

        reward_item = MenuItem.objects.filter(is_loyalty_reward=True, is_available=True).first()
        if reward_item:
            for customer in customers:
                account = getattr(customer, 'loyalty_account', None)
                if account and account.points >= 100:
                    redemption = LoyaltyRedemption.objects.create(
                        account=account, code=f'DEMO-{customer.username[:4].upper()}1',
                        reward=reward_item, used_at=self.now - timedelta(days=random.randint(1, 20)),
                    )
                    self.backdate(LoyaltyRedemption.objects, redemption.pk, self.now - timedelta(days=random.randint(21, 40)))
                    break

    # ---- expenses -----------------------------------------------------
    def seed_expenses(self):
        count = 0
        for weeks_ago in range(0, 13):
            day = self.today - timedelta(days=weeks_ago * 7 + random.randint(0, 2))
            Expense.objects.create(
                description=random.choice(['Fresh produce delivery', 'Meat & poultry supplier', 'Wine & beverages order', 'Bakery supplies']),
                category=Expense.SUPPLIER, amount=Decimal(random.randint(150, 850)),
                expense_date=day, paid=True, supplier=random.choice(['Metro Cash & Carry', 'Local Farmers Co-op', 'Selgros', 'Vinarte Distribution']),
            )
            count += 1

        for months_ago in range(0, 3):
            day = (self.today.replace(day=1) - timedelta(days=months_ago * 30 + 1)).replace(day=random.randint(25, 28))
            Expense.objects.create(
                description='Staff salaries', category=Expense.SALARY,
                amount=Decimal(random.randint(4200, 5600)), expense_date=day, paid=True,
            )
            count += 1

        for description, amount_range in [('Utilities (electricity, water, gas)', (300, 700)), ('Social media advertising', (80, 300)), ('Kitchen equipment maintenance', (100, 450))]:
            for _ in range(random.randint(1, 3)):
                day = self.today - timedelta(days=random.randint(1, 85))
                Expense.objects.create(
                    description=description, category=Expense.OTHER,
                    amount=Decimal(random.randint(*amount_range)), expense_date=day,
                    paid=random.random() < 0.9,
                )
                count += 1

        self.stdout.write(f'Created {count} expenses.')

    # ---- events -----------------------------------------------------
    def seed_events(self):
        if Event.objects.count() >= 3:
            self.stdout.write('Events already present, skipping.')
            return

        past_start = self.now - timedelta(days=18, hours=-19)
        past_event = Event.objects.create(
            title='Summer Jazz Night', description='An evening of live jazz with a special tasting menu.',
            starts_at=past_start, ends_at=past_start + timedelta(hours=3),
            capacity=50, ticket_price=Decimal('35.00'), requires_reservation=True, is_active=True,
        )
        for _ in range(13):
            ticket = Ticket.objects.create(
                event=past_event, customer_name=random.choice(RESERVATION_NAMES)[0],
                customer_email='guest@example.com', quantity=random.randint(1, 3), paid=True,
            )
            self.backdate(Ticket.objects, ticket.pk, past_start - timedelta(days=random.randint(2, 10)))

        upcoming = [
            ('Wine Pairing Dinner', 'A five-course dinner paired with wines selected by our sommelier.', 21, 19, 40, Decimal('65.00'), 18),
            ('Live Acoustic Evening', 'Live acoustic music on the terrace, light bites included.', 35, 20, 60, Decimal('20.00'), 24),
        ]
        for title, desc, days_ahead, hour, capacity, price, booked in upcoming:
            starts_at = timezone.make_aware(datetime.combine(self.today + timedelta(days=days_ahead), time(hour, 0)))
            event = Event.objects.create(
                title=title, description=desc, starts_at=starts_at, ends_at=starts_at + timedelta(hours=3),
                capacity=capacity, ticket_price=price, requires_reservation=True, is_active=True,
            )
            sold = 0
            while sold < booked:
                qty = random.randint(1, 3)
                if sold + qty > capacity:
                    break
                ticket = Ticket.objects.create(
                    event=event, customer_name=random.choice(RESERVATION_NAMES)[0],
                    customer_email='guest@example.com', quantity=qty, paid=True,
                )
                self.backdate(Ticket.objects, ticket.pk, self.now - timedelta(days=random.randint(0, 12)))
                sold += qty

        self.stdout.write('Created events and tickets.')

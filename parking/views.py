from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import TwoWheelerEntry, FourWheelerEntry
from .forms import TwoWheelerEntryForm, FourWheelerEntryForm, LoginForm
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
import random
import string
import pandas as pd
from datetime import datetime, timedelta
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ================================
# AUTHENTICATION VIEWS
# ================================

def login_view(request):
    """
    Handle user login
    """
    # If user is already logged in, redirect to homepage
    if request.user.is_authenticated:
        return redirect('homepage')
        
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome {username}!")
                return redirect("homepage")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()
    
    return render(request, "login.html", {"form": form})

def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login_view')

# ================================
# PASSWORD RESET VIEWS
# ================================

class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view
    """
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        messages.success(self.request, 
            "Password reset instructions have been sent to your email. Please check your inbox.")
        return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirmation view
    """
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, 
            "Your password has been reset successfully. You can now login with your new password.")
        return super().form_valid(form)

def password_reset_done(request):
    """
    Password reset done page
    """
    return render(request, 'password_reset_done.html')

def password_reset_complete(request):
    """
    Password reset complete page
    """
    return render(request, 'password_reset_complete.html')

# ================================
# UTILITY FUNCTIONS
# ================================

def generate_token_id(prefix):
    """
    Generate unique token ID for vehicles
    """
    while True:
        rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        token_id = f"{prefix}{rand_str}"
        # Check if token exists in either model
        if (not TwoWheelerEntry.objects.filter(token_id=token_id).exists() and 
            not FourWheelerEntry.objects.filter(token_id=token_id).exists()):
            return token_id

def calculate_amount(entry_time, exit_time, rate_per_hour):
    """
    Calculate parking amount based on duration
    """
    duration = exit_time - entry_time
    hours = max(1, int((duration.total_seconds() + 3599) // 3600))  # Round up hours
    return hours * rate_per_hour

# ================================
# PARKING MANAGEMENT VIEWS
# ================================

@login_required
def homepage(request):
    """
    Homepage view - shows dashboard with statistics
    """
    # Get current parking stats
    two_wheeler_count = TwoWheelerEntry.objects.filter(exit_time__isnull=True).count()
    four_wheeler_count = FourWheelerEntry.objects.filter(exit_time__isnull=True).count()
    
    # Get today's revenue
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue_two = TwoWheelerEntry.objects.filter(
        exit_time__isnull=False,
        exit_time__gte=today_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    today_revenue_four = FourWheelerEntry.objects.filter(
        exit_time__isnull=False,
        exit_time__gte=today_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_today_revenue = today_revenue_two + today_revenue_four
    
    context = {
        'two_wheeler_count': two_wheeler_count,
        'four_wheeler_count': four_wheeler_count,
        'total_vehicles': two_wheeler_count + four_wheeler_count,
        'today_revenue': total_today_revenue,
    }
    return render(request, 'homepage.html', context)

# ================================
# TWO WHEELER VIEWS
# ================================

@login_required
def two_wheeler_entry(request):
    """
    Handle two wheeler entry
    """
    if request.method == 'POST':
        form = TwoWheelerEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.token_id = generate_token_id('TW')
            entry.entry_time = timezone.now()
            entry.save()
            messages.success(request, f'Two-wheeler entry created successfully! Token: {entry.token_id}')
            return redirect('entry_success', token_id=entry.token_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TwoWheelerEntryForm()
    
    return render(request, 'two_wheeler_entry.html', {'form': form})

@login_required
def two_wheeler_exit_search(request):
    """
    Search page for two-wheeler exit
    """
    return render(request, 'two_wheeler_exit.html')

@login_required
def two_wheeler_exit(request, token_id):
    """
    Process two-wheeler exit
    """
    try:
        entry = TwoWheelerEntry.objects.get(token_id=token_id, exit_time__isnull=True)
        
        if request.method == 'POST':
            entry.exit_time = timezone.now()
            entry.amount = calculate_amount(entry.entry_time, entry.exit_time, 30)  # ₹30 per hour
            entry.save()
            messages.success(request, f'Exit processed successfully! Amount: ₹{entry.amount}')
            return redirect('exit_success', token_id=entry.token_id)
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'token_id': entry.token_id,
                'vehicle_number': entry.vehicle_no,
                'entry_time': entry.entry_time.isoformat(),
                'exists': True
            })
        
        # For regular GET requests
        return render(request, 'two_wheeler_exit_confirm.html', {'entry': entry})
        
    except TwoWheelerEntry.DoesNotExist:
        # AJAX response for not found
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Vehicle not found. Please check the token number.',
                'exists': False
            }, status=404)
        
        # Regular response for not found
        messages.error(request, 'Vehicle not found. Please check the token number.')
        return redirect('two_wheeler_exit_search')

# ================================
# FOUR WHEELER VIEWS
# ================================

@login_required
def four_wheeler_entry(request):
    """
    Handle four wheeler entry
    """
    if request.method == 'POST':
        form = FourWheelerEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.token_id = generate_token_id('FW')
            entry.entry_time = timezone.now()
            entry.save()
            messages.success(request, f'Four-wheeler entry created successfully! Token: {entry.token_id}')
            return redirect('entry_success', token_id=entry.token_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FourWheelerEntryForm()
    
    return render(request, 'four_wheeler_entry.html', {'form': form})

@login_required
def four_wheeler_exit_search(request):
    """
    Search page for four-wheeler exit
    """
    return render(request, 'four_wheeler_exit.html')

@login_required
def four_wheeler_exit(request, token_id):
    """
    Process four-wheeler exit
    """
    try:
        entry = FourWheelerEntry.objects.get(token_id=token_id, exit_time__isnull=True)
        
        if request.method == 'POST':
            entry.exit_time = timezone.now()
            entry.amount = calculate_amount(entry.entry_time, entry.exit_time, 50)  # ₹50 per hour
            entry.save()
            messages.success(request, f'Exit processed successfully! Amount: ₹{entry.amount}')
            return redirect('exit_success', token_id=entry.token_id)
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'token_id': entry.token_id,
                'vehicle_number': entry.vehicle_no,
                'entry_time': entry.entry_time.isoformat(),
                'exists': True
            })
        
        # For regular GET requests
        return render(request, 'four_wheeler_exit_confirm.html', {'entry': entry})
        
    except FourWheelerEntry.DoesNotExist:
        # AJAX response for not found
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Vehicle not found. Please check the token number.',
                'exists': False
            }, status=404)
        
        # Regular response for not found
        messages.error(request, 'Vehicle not found. Please check the token number.')
        return redirect('four_wheeler_exit_search')

# ================================
# SUCCESS PAGES
# ================================

@login_required
def entry_success(request, token_id):
    """
    Show success page after vehicle entry
    """
    return render(request, 'entry_success.html', {'token_id': token_id})

@login_required
def exit_success(request, token_id):
    """
    Show success page after vehicle exit with payment details
    """
    # Determine which model to use based on token prefix
    if token_id.startswith('TW'):
        entry = get_object_or_404(TwoWheelerEntry, token_id=token_id)
        vehicle_type = "Two Wheeler"
        rate = "₹30 per hour"
    else:
        entry = get_object_or_404(FourWheelerEntry, token_id=token_id)
        vehicle_type = "Four Wheeler"
        rate = "₹50 per hour"
    
    context = {
        'entry': entry,
        'vehicle_type': vehicle_type,
        'rate': rate,
    }
    return render(request, 'exit_success.html', context)

# ================================
# REPORTS & ANALYTICS VIEWS
# ================================

@login_required
def reports_analytics(request):
    """
    Reports and analytics dashboard with charts and filters
    """
    # Get date range from request or default to last 7 days
    date_filter = request.GET.get('date_filter', '7days')
    
    end_date = timezone.now()
    if date_filter == 'today':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_filter == 'yesterday':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_date = start_date + timedelta(days=1)
    elif date_filter == '30days':
        start_date = end_date - timedelta(days=30)
    else:  # 7days default
        start_date = end_date - timedelta(days=7)
    
    # Get current parking stats
    two_wheeler_count = TwoWheelerEntry.objects.filter(exit_time__isnull=True).count()
    four_wheeler_count = FourWheelerEntry.objects.filter(exit_time__isnull=True).count()
    
    # Get revenue data for the period
    two_wheeler_revenue = TwoWheelerEntry.objects.filter(
        exit_time__isnull=False,
        entry_time__gte=start_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    four_wheeler_revenue = FourWheelerEntry.objects.filter(
        exit_time__isnull=False,
        entry_time__gte=start_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_revenue = two_wheeler_revenue + four_wheeler_revenue
    
    # Get vehicle counts for the period
    two_wheeler_entries = TwoWheelerEntry.objects.filter(entry_time__gte=start_date).count()
    four_wheeler_entries = FourWheelerEntry.objects.filter(entry_time__gte=start_date).count()
    total_entries = two_wheeler_entries + four_wheeler_entries
    
    # Generate charts
    revenue_chart = generate_revenue_chart(start_date, end_date)
    vehicle_distribution_chart = generate_vehicle_distribution_chart(start_date, end_date)
    hourly_trend_chart = generate_hourly_trend_chart(start_date, end_date)
    
    context = {
        'page_title': 'Reports & Analytics',
        'user': request.user,
        'two_wheeler_count': two_wheeler_count,
        'four_wheeler_count': four_wheeler_count,
        'total_vehicles': two_wheeler_count + four_wheeler_count,
        'two_wheeler_revenue': two_wheeler_revenue,
        'four_wheeler_revenue': four_wheeler_revenue,
        'total_revenue': total_revenue,
        'two_wheeler_entries': two_wheeler_entries,
        'four_wheeler_entries': four_wheeler_entries,
        'total_entries': total_entries,
        'date_filter': date_filter,
        'revenue_chart': revenue_chart,
        'vehicle_distribution_chart': vehicle_distribution_chart,
        'hourly_trend_chart': hourly_trend_chart,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
    }
    return render(request, 'reports_analytics.html', context)

@login_required
def generate_daily_report(request):
    """
    Generate daily report and export to Excel
    """
    return generate_excel_report(request, 'daily')

@login_required
def generate_weekly_report(request):
    """
    Generate weekly report and export to Excel
    """
    return generate_excel_report(request, 'weekly')

@login_required
def generate_monthly_report(request):
    """
    Generate monthly report and export to Excel
    """
    return generate_excel_report(request, 'monthly')

@login_required
def export_to_excel(request):
    """
    Export current view data to Excel
    """
    return generate_excel_report(request, 'custom')

# ================================
# CHART GENERATION FUNCTIONS
# ================================

def generate_revenue_chart(start_date, end_date):
    """
    Generate revenue trend chart
    """
    try:
        # Get daily revenue data
        dates = []
        two_wheeler_revenue = []
        four_wheeler_revenue = []
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            two_rev = TwoWheelerEntry.objects.filter(
                exit_time__isnull=False,
                exit_time__gte=current_date,
                exit_time__lt=next_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            four_rev = FourWheelerEntry.objects.filter(
                exit_time__isnull=False,
                exit_time__gte=current_date,
                exit_time__lt=next_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            dates.append(current_date)
            two_wheeler_revenue.append(two_rev)
            four_wheeler_revenue.append(four_rev)
            
            current_date = next_date
        
        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(dates, two_wheeler_revenue, label='Two Wheelers', marker='o', linewidth=2, color='#10b981')
        plt.plot(dates, four_wheeler_revenue, label='Four Wheelers', marker='s', linewidth=2, color='#ef4444')
        plt.title('Daily Revenue Trend', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Revenue (₹)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        return generate_placeholder_chart("Revenue Chart - Data Not Available")

def generate_vehicle_distribution_chart(start_date, end_date):
    """
    Generate vehicle distribution pie chart
    """
    try:
        two_wheeler_count = TwoWheelerEntry.objects.filter(entry_time__gte=start_date).count()
        four_wheeler_count = FourWheelerEntry.objects.filter(entry_time__gte=start_date).count()
        
        # Only generate chart if we have data
        if two_wheeler_count == 0 and four_wheeler_count == 0:
            return generate_placeholder_chart("No Vehicle Data Available")
        
        plt.figure(figsize=(8, 6))
        labels = ['Two Wheelers', 'Four Wheelers']
        sizes = [two_wheeler_count, four_wheeler_count]
        colors = ['#10b981', '#ef4444']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Vehicle Distribution', fontsize=14, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        return generate_placeholder_chart("Vehicle Distribution - Error")

def generate_hourly_trend_chart(start_date, end_date):
    """
    Generate hourly trend chart
    """
    try:
        hours = list(range(24))
        two_wheeler_hourly = [0] * 24
        four_wheeler_hourly = [0] * 24
        
        # Get two wheeler entries by hour
        two_entries = TwoWheelerEntry.objects.filter(entry_time__gte=start_date)
        for entry in two_entries:
            hour = entry.entry_time.hour
            two_wheeler_hourly[hour] += 1
        
        # Get four wheeler entries by hour
        four_entries = FourWheelerEntry.objects.filter(entry_time__gte=start_date)
        for entry in four_entries:
            hour = entry.entry_time.hour
            four_wheeler_hourly[hour] += 1
        
        plt.figure(figsize=(10, 6))
        plt.bar([h - 0.2 for h in hours], two_wheeler_hourly, width=0.4, label='Two Wheelers', color='#10b981')
        plt.bar([h + 0.2 for h in hours], four_wheeler_hourly, width=0.4, label='Four Wheelers', color='#ef4444')
        plt.title('Hourly Entry Trend', fontsize=14, fontweight='bold')
        plt.xlabel('Hour of Day')
        plt.ylabel('Number of Vehicles')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(hours)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
        
        return graphic
    except Exception as e:
        return generate_placeholder_chart("Hourly Trend - Error")

def generate_placeholder_chart(message):
    """
    Generate a placeholder chart when data is not available
    """
    plt.figure(figsize=(10, 6))
    plt.text(0.5, 0.5, message, ha='center', va='center', transform=plt.gca().transAxes, fontsize=16)
    plt.axis('off')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    plt.close()
    
    return graphic

def generate_excel_report(request, report_type):
    """
    Generate Excel report based on type
    """
    end_date = timezone.now()
    
    if report_type == 'daily':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        filename = f"daily_report_{end_date.strftime('%Y%m%d')}.xlsx"
    elif report_type == 'weekly':
        start_date = end_date - timedelta(days=7)
        filename = f"weekly_report_{end_date.strftime('%Y%m%d')}.xlsx"
    elif report_type == 'monthly':
        start_date = end_date - timedelta(days=30)
        filename = f"monthly_report_{end_date.strftime('%Y%m')}.xlsx"
    else:  # custom
        date_filter = request.GET.get('date_filter', '7days')
        if date_filter == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == 'yesterday':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_date = start_date + timedelta(days=1)
        elif date_filter == '30days':
            start_date = end_date - timedelta(days=30)
        else:  # 7days
            start_date = end_date - timedelta(days=7)
        filename = f"parking_report_{end_date.strftime('%Y%m%d')}.xlsx"
    
    # Get data
    two_wheeler_data = TwoWheelerEntry.objects.filter(entry_time__gte=start_date)
    four_wheeler_data = FourWheelerEntry.objects.filter(entry_time__gte=start_date)
    
    # Create Excel file
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Metric': ['Total Two Wheelers', 'Total Four Wheelers', 'Total Vehicles', 
                      'Two Wheeler Revenue', 'Four Wheeler Revenue', 'Total Revenue',
                      'Report Period', 'Generated On'],
            'Value': [
                two_wheeler_data.count(),
                four_wheeler_data.count(),
                two_wheeler_data.count() + four_wheeler_data.count(),
                two_wheeler_data.filter(exit_time__isnull=False).aggregate(Sum('amount'))['amount__sum'] or 0,
                four_wheeler_data.filter(exit_time__isnull=False).aggregate(Sum('amount'))['amount__sum'] or 0,
                (two_wheeler_data.filter(exit_time__isnull=False).aggregate(Sum('amount'))['amount__sum'] or 0) +
                (four_wheeler_data.filter(exit_time__isnull=False).aggregate(Sum('amount'))['amount__sum'] or 0),
                f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Two Wheeler sheet
        two_wheeler_list = list(two_wheeler_data.values(
            'token_id', 'vehicle_no', 'phone_number', 'entry_time', 'exit_time', 'amount'
        ))
        if two_wheeler_list:
            df_two = pd.DataFrame(two_wheeler_list)
            df_two.to_excel(writer, sheet_name='Two Wheelers', index=False)
        
        # Four Wheeler sheet
        four_wheeler_list = list(four_wheeler_data.values(
            'token_id', 'vehicle_no', 'phone_number', 'entry_time', 'exit_time', 'amount'
        ))
        if four_wheeler_list:
            df_four = pd.DataFrame(four_wheeler_list)
            df_four.to_excel(writer, sheet_name='Four Wheelers', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    messages.success(request, f'Report generated successfully!')
    return response





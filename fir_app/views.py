import google.generativeai as genai
from .utils import draft_fir_with_ai
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import ComplaintDetails, AccusedDetails, FIRRecord
from .forms import CustomUserCreationForm, CustomLoginForm, ComplaintDetailsForm, AccusedDetailsForm

# --- AUTHENTICATION VIEWS (Keep these as they are) ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome to FIR Draft!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'fir_app/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"You are now logged in as {username}.")
                return redirect('home')
    else:
        form = CustomLoginForm()
    return render(request, 'fir_app/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


def about_view(request):
    return render(request, 'fir_app/about.html')


def contact_view(request):
    return render(request, 'fir_app/contact.html')


# --- NEW DASHBOARD VIEW ---

@login_required(login_url='login')
def dashboard_view(request):
    # 1. Initialize empty forms
    complaint_form = ComplaintDetailsForm()
    accused_form = AccusedDetailsForm()

    # 2. Handle Form Submissions
    if request.method == 'POST':
        if 'submit_complaint' in request.POST:
            complaint_form = ComplaintDetailsForm(request.POST)
            if complaint_form.is_valid():
                complaint = complaint_form.save(commit=False)
                complaint.user = request.user
                complaint.save()
                messages.success(request, "Complaint details saved successfully!")
                return redirect(f"{reverse('home')}?tab=accused")
        
        elif 'submit_accused' in request.POST:
            accused_form = AccusedDetailsForm(request.POST)
            if accused_form.is_valid():
                latest_complaint = ComplaintDetails.objects.filter(user=request.user).order_by('-created_at').first()
                if not latest_complaint:
                    messages.error(request, "Please save complaint details before adding accused information.")
                    return redirect('home')
                accused = accused_form.save(commit=False)
                accused.complaint = latest_complaint
                accused.save()
                messages.success(request, "Accused details saved successfully!")
                return redirect(f"{reverse('home')}?tab=generated")

    # Get user's data for dashboard stats
    all_complaints = ComplaintDetails.objects.filter(user=request.user)
    fir_records = FIRRecord.objects.filter(complaint__user=request.user).order_by('-generated_date')
    latest_unrecorded_complaint = ComplaintDetails.objects.filter(user=request.user, fir_record__isnull=True).order_by('-created_at').first()
    
    # Calculate statistics
    total_drafts = all_complaints.count()
    generated_firs = fir_records.count()
    pending_drafts = all_complaints.filter(fir_record__isnull=True).count()
    total_complaints = total_drafts
    
    # Get incident type statistics
    incident_types = {}
    for record in fir_records:
        incident = record.complaint.incident_type
        incident_types[incident] = incident_types.get(incident, 0) + 1
    
    # Recent FIRs (limit to 5)
    recent_firs = fir_records[:5]
    
    context = {
        'complaint_form': complaint_form,
        'accused_form': accused_form,
        'fir_records': fir_records,
        'latest_unrecorded_complaint': latest_unrecorded_complaint,
        'total_drafts': total_drafts,
        'generated_firs': generated_firs,
        'pending_drafts': pending_drafts,
        'total_complaints': total_complaints,
        'incident_types': incident_types,
        'recent_firs': recent_firs,
        'username': request.user.first_name or request.user.username,
    }
    
    if request.GET.get('tab') in {'complaint', 'accused', 'generated', 'records', 'overview'}:
        context['active_tab'] = request.GET['tab']
    else:
        context['active_tab'] = 'overview'

    return render(request, 'fir_app/dashboard.html', context)
     
    # ... rest of your code

@login_required(login_url='login')
def generate_fir_view(request):
    if request.method == 'POST':
        latest_complaint = ComplaintDetails.objects.filter(user=request.user, fir_record__isnull=True).order_by('-created_at').first()

        if not latest_complaint:
            messages.error(request, "You must submit a Complaint Details form first.")
            return redirect('home')

        accused_list = latest_complaint.accused_persons.all()
        generated_text = draft_fir_with_ai(latest_complaint, accused_list)

        if generated_text.startswith("ERROR:"):
            messages.error(request, f"AI Generation Failed: {generated_text}")
        else:
            FIRRecord.objects.create(
                complaint=latest_complaint,
                generated_text=generated_text
            )
            messages.success(request, "Your FIR has been successfully drafted by AI!")
            return redirect(f"{reverse('home')}?tab=records")

        if generated_text.startswith("ERROR:"):
            messages.error(request, f"AI Generation Failed: {generated_text}")

    return redirect(f"{reverse('home')}?tab=generated")

@login_required(login_url='login')
def delete_fir_record_view(request, fir_id):
    fir = get_object_or_404(FIRRecord, id=fir_id, complaint__user=request.user)
    fir.delete()
    messages.success(request, "FIR record deleted successfully.")
    return redirect(f"{reverse('home')}?tab=records")


@login_required(login_url='login')
def fir_detail_view(request, fir_id):
    # SECURITY CHECK: This enforces the "Authority"
    # It searches for the FIR, but ONLY if the logged-in user (request.user) owns the complaint.
    # If a hacker tries to guess another user's FIR ID, Django will block them with a 404 Error.
    fir = get_object_or_404(FIRRecord, id=fir_id, complaint__user=request.user)
    
    return render(request, 'fir_app/fir_detail.html', {'fir': fir})
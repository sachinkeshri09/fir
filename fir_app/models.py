import uuid
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User

class ComplaintDetails(models.Model):
    # Links the complaint to the logged-in user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    
    # Core Details
    complainant_name = models.CharField(max_length=200) 
    district = models.CharField(max_length=100)        
    police_station = models.CharField(max_length=100)  
    incident_date = models.DateField()
    incident_time = models.TimeField()
    location = models.CharField(max_length=255)
    incident_type = models.CharField(max_length=100) # e.g., Theft, Assault
    description = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    id_proof = models.CharField(max_length=200, blank=True, null=True)
    id_proof_number = models.CharField(max_length=100, blank=True, null=True)
    language_preference = models.CharField(
        max_length=20,
        choices=[
            ('English', 'English'),
            ('Hindi', 'Hindi'),
        ],
        default='English',
        help_text='Preferred language for FIR drafting'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint #{self.id} by {self.user.username} - {self.incident_type}"


class AccusedDetails(models.Model):
    # Links directly to the Complaint. 'related_name' allows us to easily fetch all accused for a single complaint.
    complaint = models.ForeignKey(ComplaintDetails, on_delete=models.CASCADE, related_name='accused_persons')
    
    name = models.CharField(max_length=150, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    physical_description = models.TextField(blank=True, null=True)
    relationship_to_victim = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Accused: {self.name or 'Unknown'} (Complaint #{self.complaint.id})"


class FIRRecord(models.Model):
    # OneToOneField because one Complaint should logically generate exactly one final FIR record.
    complaint = models.OneToOneField(ComplaintDetails, on_delete=models.CASCADE, related_name='fir_record')
    
    fir_number = models.CharField(max_length=50, unique=True, blank=True)
    generated_text = models.TextField()
    generated_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate a unique FIR number if it doesn't exist yet
        if not self.fir_number:
            date_str = datetime.now().strftime("%Y%m%d")
            unique_id = str(uuid.uuid4().hex)[:6].upper()
            self.fir_number = f"FIR-{date_str}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.fir_number
from django.contrib import admin
from .models import ComplaintDetails, AccusedDetails, FIRRecord

# These "Inlines" allow us to edit Accused and FIR data directly inside the Complaint view
class AccusedDetailsInline(admin.StackedInline):
    model = AccusedDetails
    extra = 1 # Shows one blank extra form by default

class FIRRecordInline(admin.StackedInline):
    model = FIRRecord
    extra = 0 

@admin.register(ComplaintDetails)
class ComplaintDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'incident_type', 'incident_date', 'location', 'created_at')
    list_filter = ('incident_type', 'incident_date')
    search_fields = ('user__username', 'location', 'incident_type')
    inlines = [AccusedDetailsInline, FIRRecordInline]

@admin.register(AccusedDetails)
class AccusedDetailsAdmin(admin.ModelAdmin):
    list_display = ('name', 'complaint', 'age', 'relationship_to_victim')
    search_fields = ('name', 'complaint__id')

@admin.register(FIRRecord)
class FIRRecordAdmin(admin.ModelAdmin):
    list_display = ('fir_number', 'complaint', 'generated_date')
    readonly_fields = ('fir_number', 'generated_date')
    search_fields = ('fir_number',)
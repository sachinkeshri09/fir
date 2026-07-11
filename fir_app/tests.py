from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import ComplaintDetailsForm
from .models import ComplaintDetails, FIRRecord
from .utils import build_formal_fir_text, sanitize_generated_fir_text


class ComplaintDetailsFormTests(TestCase):
    def test_complaint_form_accepts_contact_and_id_fields(self):
        user = User.objects.create_user(username='tester', password='secret123')
        form_data = {
            'complainant_name': 'Asha Kumar',
            'district': 'Bengaluru',
            'police_station': 'Cubbon Park',
            'incident_date': date(2026, 7, 10),
            'incident_time': time(14, 30),
            'location': 'MG Road',
            'incident_type': 'Theft/Robbery',
            'language_preference': 'English',
            'description': 'Mobile phone stolen during the evening.',
            'contact_number': '9876543210',
            'email': 'asha@example.com',
            'id_proof': 'Aadhaar Card',
            'id_proof_number': '123456789012',
        }

        form = ComplaintDetailsForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        complaint = form.save(commit=False)
        complaint.user = user
        complaint.save()

        self.assertEqual(complaint.contact_number, '9876543210')
        self.assertEqual(complaint.email, 'asha@example.com')
        self.assertEqual(complaint.id_proof, 'Aadhaar Card')
        self.assertEqual(complaint.id_proof_number, '123456789012')

    def test_complaint_form_accepts_other_incident_type(self):
        user = User.objects.create_user(username='tester2', password='secret123')
        form_data = {
            'complainant_name': 'Ravi Patel',
            'district': 'Pune',
            'police_station': 'Shivaji Nagar',
            'incident_date': date(2026, 7, 11),
            'incident_time': time(10, 15),
            'location': 'FC Road',
            'incident_type': 'Other',
            'other_incident_type': 'Stolen Bicycle',
            'language_preference': 'English',
            'description': 'Bicycle was taken from the parking area.',
            'contact_number': '9123456780',
            'email': 'ravi@example.com',
            'id_proof': 'PAN Card',
            'id_proof_number': 'ABCDE1234F',
        }

        form = ComplaintDetailsForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        complaint = form.save(commit=False)
        complaint.user = user
        complaint.save()

        self.assertEqual(complaint.incident_type, 'Stolen Bicycle')
        self.assertEqual(complaint.id_proof, 'PAN Card')


class StaticPageTests(TestCase):
    def test_about_page_loads(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'About')

    def test_contact_page_loads(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact')


class DashboardWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.client.force_login(self.user)

    def test_complaint_save_redirects_to_accused_details(self):
        response = self.client.post(reverse('home'), {
            'submit_complaint': '1',
            'complainant_name': 'Asha Kumar',
            'district': 'Bengaluru',
            'police_station': 'Cubbon Park',
            'incident_date': '2026-07-10',
            'incident_time': '14:30',
            'location': 'MG Road',
            'incident_type': 'Theft/Robbery',
            'description': 'Mobile phone stolen during the evening.',
            'contact_number': '9876543210',
            'email': 'asha@example.com',
            'id_proof': 'Aadhaar Card',
        })

        self.assertRedirects(response, reverse('home') + '?tab=accused')
        self.assertTrue(ComplaintDetails.objects.filter(user=self.user).exists())

    def test_generate_fir_redirects_to_generated_tab_and_creates_record(self):
        complaint = ComplaintDetails.objects.create(
            user=self.user,
            complainant_name='Asha Kumar',
            district='Bengaluru',
            police_station='Cubbon Park',
            incident_date=date(2026, 7, 10),
            incident_time=time(14, 30),
            location='MG Road',
            incident_type='Theft/Robbery',
            description='Mobile phone stolen during the evening.',
            contact_number='9876543210',
            email='asha@example.com',
            id_proof='Aadhaar Card',
        )

        response = self.client.post(reverse('generate_fir'))

        self.assertRedirects(response, reverse('home') + '?tab=records')
        self.assertTrue(FIRRecord.objects.filter(complaint=complaint).exists())

    def test_delete_fir_record_removes_it(self):
        complaint = ComplaintDetails.objects.create(
            user=self.user,
            complainant_name='Asha Kumar',
            district='Bengaluru',
            police_station='Cubbon Park',
            incident_date=date(2026, 7, 10),
            incident_time=time(14, 30),
            location='MG Road',
            incident_type='Theft/Robbery',
            description='Mobile phone stolen during the evening.',
            contact_number='9876543210',
            email='asha@example.com',
            id_proof='Aadhaar Card',
        )
        fir_record = FIRRecord.objects.create(complaint=complaint, generated_text='Sample FIR text')

        response = self.client.post(reverse('delete_fir_record', args=[fir_record.id]))

        self.assertRedirects(response, reverse('home') + '?tab=records')
        self.assertFalse(FIRRecord.objects.filter(id=fir_record.id).exists())


class FormalFIRFormattingTests(TestCase):
    def test_build_formal_fir_text_includes_police_style_sections(self):
        complaint = type('Complaint', (), {
            'district': 'Bengaluru',
            'police_station': 'Cubbon Park',
            'complainant_name': 'Asha Kumar',
            'contact_number': '9876543210',
            'email': 'asha@example.com',
            'id_proof': 'Aadhaar Card',
            'incident_type': 'Theft/Robbery',
            'incident_date': '2026-07-10',
            'incident_time': '14:30',
            'location': 'MG Road',
            'description': 'Mobile phone stolen during the evening.'
        })()
        accused_list = []

        text = build_formal_fir_text(complaint, accused_list)

        self.assertIn('FIRST INFORMATION REPORT', text.upper())
        self.assertIn('COMPLAINANT DETAILS', text.upper())
        self.assertIn('INCIDENT DETAILS', text.upper())
        self.assertIn('NARRATION OF INCIDENT', text.upper())

    def test_sanitize_generated_fir_text_removes_signature_block(self):
        raw_text = "FIRST INFORMATION REPORT\n\nSignature of Complainant\nName: Asha Kumar"

        cleaned = sanitize_generated_fir_text(raw_text)

        self.assertNotIn('signature of complainant', cleaned.lower())

    def test_sanitize_generated_fir_text_removes_duplicate_fir_header(self):
        raw_text = "FIRST INFORMATION REPORT\n\nFIR No: FIR-20260710-123456\nDate: 10 July 2026\nTime: 14:30\n\nNarration of incident"

        cleaned = sanitize_generated_fir_text(raw_text)

        self.assertNotIn('fir no:', cleaned.lower())
        self.assertNotIn('date:', cleaned.lower())
        self.assertNotIn('time:', cleaned.lower())

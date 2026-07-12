# fir_app/utils.py
import logging
import os
import re
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from google import genai as new_genai
    HAS_NEW_GENAI = True
except ImportError:
    new_genai = None
    HAS_NEW_GENAI = False


def sanitize_generated_fir_text(text):
    if not text:
        return text

    cleaned = re.sub(r"\n\s*signature of the complainant.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\n\s*signature of complainant.*", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\n\s*name: .*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n\s*fir no:.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n\s*date:.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n\s*time:.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace('*', '')
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def build_formal_fir_text(complaint, accused_list):
    accused_info = ""
    if accused_list.exists() if hasattr(accused_list, 'exists') else False:
        accused_info = "\nDESCRIPTION OF ACCUSED (IF KNOWN)\n"
        for idx, accused in enumerate(accused_list, 1):
            name = accused.name or 'Unknown'
            age = accused.age or 'Unknown'
            desc = accused.physical_description or 'Not provided'
            rel = accused.relationship_to_victim or 'Not provided'
            accused_info += f"{idx}. Name: {name}; Age: {age}; Description: {desc}; Relationship to Victim: {rel}\n"

    return f"""FIRST INFORMATION REPORT

Police Station: {complaint.police_station}
District: {complaint.district}
FIR No: __________
Date: __________
Time: __________

COMPLAINANT DETAILS
Name: {complaint.complainant_name}
Contact Number: {complaint.contact_number or 'Not provided'}
Email: {complaint.email or 'Not provided'}
ID Proof: {complaint.id_proof or 'Not provided'}

INCIDENT DETAILS
Type of Offence: {complaint.incident_type}
Date of Incident: {complaint.incident_date}
Time of Incident: {complaint.incident_time}
Place of Incident: {complaint.location}

NARRATION OF INCIDENT
On {complaint.incident_date}, at about {complaint.incident_time}, at {complaint.location}, the complainant reported that {complaint.description}. The matter was brought to the notice of the police station for necessary action.

{accused_info}
Signature of Complainant
Name: {complaint.complainant_name}
"""


def draft_fir_with_ai(complaint, accused_list):
    """
    Takes a ComplaintDetails object and a QuerySet of AccusedDetails.
    Calls the Gemini API and returns the generated FIR text.
    """
    try:
        api_key = settings.GEMINI_API_KEY or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return "ERROR: Gemini/Google API key not configured in settings"

        def build_prompt():
            accused_info = ""
            if accused_list.exists():
                accused_info = "Accused Details:\n"
                for idx, accused in enumerate(accused_list, 1):
                    name = accused.name or 'Unknown'
                    age = accused.age or 'Unknown'
                    desc = accused.physical_description or 'None provided'
                    rel = accused.relationship_to_victim or 'None'
                    accused_info += f"{idx}. Name: {name}, Age: {age}, Description: {desc}, Relationship: {rel}\n"

            language_pref = getattr(complaint, 'language_preference', 'English') or 'English'
            language_instruction = 'Write the final FIR in fluent English.'
            if language_pref.lower() == 'hindi':
                language_instruction = 'Write the final FIR in fluent Hindi, using Devanagari script, while keeping the format formal and professional.'

            return f"""Act as an expert Indian Police Station House Officer. Write a formal FIR using a legal-police style layout.

IMPORTANT FORMAT RULES:
- Start with 'FIRST INFORMATION REPORT'
- Include clear sections: 'COMPLAINANT DETAILS', 'INCIDENT DETAILS', 'NARRATION OF INCIDENT', and 'DESCRIPTION OF ACCUSED (IF KNOWN)'
- Use formal, factual, and concise police language
- Do not use bullet points; use short paragraphs and labeled sections
- Keep it realistic and professional
- {language_instruction}

STATION DETAILS:
District: {complaint.district}
Police Station: {complaint.police_station}

COMPLAINANT DETAILS:
Name: {complaint.complainant_name}
Contact Number: {complaint.contact_number or 'Not provided'}
Email: {complaint.email or 'Not provided'}
ID Proof: {complaint.id_proof or 'Not provided'}

INCIDENT DETAILS:
Type of Offence: {complaint.incident_type}
Date of Incident: {complaint.incident_date}
Time of Incident: {complaint.incident_time}
Place of Incident: {complaint.location}

NARRATION OF INCIDENT:
{complaint.description}

{accused_info}

Write the final FIR in a proper formal format as used by Indian police."""

        prompt = build_prompt()

        if not HAS_NEW_GENAI:
            return "ERROR: No supported Gemini client installed. Install google-genai."

        os.environ.setdefault('GOOGLE_API_KEY', api_key)
        client = new_genai.Client()
        response = client.responses.create(
            model='gemini-3.1-flash-lite',
            input=prompt,
        )
        generated_text = getattr(response, 'output_text', None)
        if not generated_text and hasattr(response, 'output') and response.output:
            for output_item in response.output:
                if hasattr(output_item, 'content') and output_item.content:
                    for content_item in output_item.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            generated_text = str(content_item.text)
                            break
                    if generated_text:
                        break
        if not generated_text:
            generated_text = str(response)
        return sanitize_generated_fir_text(generated_text)
        
    except Exception as e:
        logger.error(f"FIR Generation Error: {str(e)}", exc_info=True)
        return f"ERROR: {str(e)}"
# fir_app/utils.py
import google.generativeai as genai
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)


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
        # Configure the API with your secure key
        api_key = settings.GEMINI_API_KEY
        
        if not api_key:
            return "ERROR: Gemini API key not configured in settings"
        
        genai.configure(api_key=api_key)
        
        # Try multiple model names in order of preference
        models_to_try = ['gemini-3.1-flash-lite', 'gemini-3.1', 'gemini-2.1', 'gemini-1.0']
        
        model = None
        last_error = None
        
        # First, try to get list of available models
        try:
            available_models = genai.list_models()
            available_model_names = []
            
            for m in available_models:
                # Check if model supports generateContent
                if hasattr(m, 'supported_generation_methods'):
                    if 'generateContent' in [method.name for method in m.supported_generation_methods]:
                        available_model_names.append(m.name)
            
            if available_model_names:
                # Use the first available model that supports generateContent
                model_name = available_model_names[0]
                model = genai.GenerativeModel('gemini-3.1-flash-lite')  # Use the first available model
                logger.info(f"Using model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not list models: {str(e)}")
            last_error = e
        
        # If list_models failed, try hardcoded models
        if not model:
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"Using fallback model: {model_name}")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_name} not available: {str(e)}")
                    continue
        
        if not model:
            return f"ERROR: No available Gemini models found. Last error: {str(last_error)}"

        # Format the accused details if any exist
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

        # Construct the System Prompt
        prompt = f"""Act as an expert Indian Police Station House Officer. Write a formal FIR using a legal-police style layout.

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

        # Generate content
        response = model.generate_content(prompt)
        return sanitize_generated_fir_text(response.text)
        
    except Exception as e:
        logger.error(f"FIR Generation Error: {str(e)}", exc_info=True)
        return f"ERROR: {str(e)}"
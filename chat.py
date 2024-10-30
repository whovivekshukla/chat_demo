from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from typing import Dict
from datetime import datetime, timedelta
import requests
from openai import OpenAI
from datetime import datetime as dt
from tools import available_tools, execute_tool

app = FastAPI()
client = OpenAI()

class ChatMessage(BaseModel):
    content: str

SURVEY_JSON = {
    "Survey": {
        "Title": "Health New England Member Survey",
        "Type": "Healthcare Access Survey",
        "Questions": [
            {
                "QuestionID": 1,
                "QuestionText": "Would you be willing to take a brief survey about your recent healthcare experiences? Your input helps us improve the care and services we offer. Options: Yes, No",
                "Options": ["Yes", "No"],
                "SkipLogic": {"No": "End"}
            },
            {
                "QuestionID": 2,
                "QuestionText": "How satisfied are you with your ability to find and schedule care when you need it? Options: 1 (Not satisfied at all) to 5 (Very satisfied)",
                "Scale": {"Min": 1, "Max": 5},
                "Options": {
                    "1": "Not satisfied at all",
                    "5": "Very satisfied"
                },
                "SkipLogic": {"1": "Q3"}
            },
            {
                "QuestionID": 3,
                "QuestionText": "Can you tell us more about the challenges you've experienced? Options include: Long wait times to get appointments, Difficulty finding available providers, Limited provider options in my area, Other (please specify)",
                "Options": [
                    "Long wait times to get appointments",
                    "Difficulty finding available providers",
                    "Limited provider options in my area",
                    "Other (please specify)"
                ],
                "MultiSelect": True,
                "NextQuestion": "Q4"
            },
            {
                "QuestionID": 4,
                "QuestionText": "Let's see if I can help you find an available provider now. What type of care are you looking for? Options: Primary Care, Cardiology, Dermatology, Mental Health, Orthopedics, Other",
                "Options": [
                    "Primary Care",
                    "Cardiology",
                    "Dermatology",
                    "Mental Health",
                    "Orthopedics",
                    "Other"
                ],
            },
        ],
   
    }
}

PROVIDERS = [
    {"name": "Dr. Sarah Johnson", "specialty": "A Therapist"},
    {"name": "Dr. Michael Chen", "specialty": "Internal Medicine"},
    {"name": "Dr. Emily Williams", "specialty": "Family Medicine"},
    {"name": "Dr. James Rodriguez", "specialty": "General Practice"},
    {"name": "Dr. Lisa Anderson", "specialty": "Internal Medicine"}
]

SUPPORTED_LANGUAGES = {
    "english": {"code": "en", "name": "English"},
    "spanish": {"code": "es", "name": "Spanish"},
    "español": {"code": "es", "name": "Spanish"},
    "hindi": {"code": "hi", "name": "Hindi"},
    "हिंदी": {"code": "hi", "name": "Hindi"},
    "chinese": {"code": "zh", "name": "Chinese"},
    "中文": {"code": "zh", "name": "Chinese"},
    "french": {"code": "fr", "name": "French"},
    "français": {"code": "fr", "name": "French"}
}

# Store session state
sessions = {}

def get_question_by_id(question_id):
    for question in SURVEY_JSON["Survey"]["Questions"]:
        if question["QuestionID"] == question_id:
            return question
    return None

def validate_response(question, response, language):
    if question is None or language is None:
        print("validate_response: question or language is None")
        return False

    system_prompt = f"""
    You are an AI assistant helping to validate survey responses. 
    Your task is to determine if a given response is valid for the question asked.
    Consider ranges in options, such as "5 to 9", and validate if the response falls within any specified range.
    When matching names, if only the first name is provided and it matches a single doctor, consider it valid. 
    However, if multiple doctors share the same first name, ensure the surname is also matched.
    Respond with only 'true' if the response is valid, or 'false' if it's invalid.
    
    IMPORTANT: The user is responding in {language['name']}. Consider responses valid if they match the meaning in any language.
    """

    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {question.get('Options', question.get('Scale', 'Any response'))}
    User response: {response}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0
        )
        return ai_response.choices[0].message.content.lower() == 'true'
    except Exception as e:
        return False

def get_next_question_id(current_question_id, user_response, language):
    current_question = get_question_by_id(current_question_id)
    if current_question is None:
        print("get_next_question_id: current_question is None")
        return None

    interpreted_response = interpret_response(current_question, user_response, language)
    
    if current_question_id == 8:
        return None
    if "SkipLogic" in current_question:
        next_question_id = current_question["SkipLogic"].get(interpreted_response)
        if next_question_id:
            return int(next_question_id[1:])
    
    questions = SURVEY_JSON["Survey"]["Questions"]
    current_index = next((i for i, q in enumerate(questions) if q["QuestionID"] == current_question_id), -1)
    if current_index < len(questions) - 1:
        return questions[current_index + 1]["QuestionID"]
    return None

def interpret_response(question, response, language):
    if question is None or language is None:
        print("interpret_response: question or language is None")
        return 'INVALID'

    system_prompt = f"""
    You are an AI assistant helping to interpret survey responses. 
    Your task is to map the given response to the closest valid option for the question.
    Respond with only the mapped option, or 'INVALID' if no mapping is possible.
    
    IMPORTANT: The user is responding in {language['name']}. Map their response to the English option that matches the meaning.
    """

    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {question.get('Options', question.get('Scale', 'Any response'))}
    User response: {response}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0
        )
        return ai_response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def validate_time_format(time_str):
    try:
        dt.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def send_appointment_email(patient_name, doctor_name, appointment_date, appointment_time):
    url = "https://notification-api-development.azo.dev/api/notifications/email"
    
    headers = {
        "api_key": "3e9583ee-5ecb-40bc-be50-2d01ef30faed",
        "organization_code": "dev-care2u",
        "Content-Type": "application/json"
    }
    
    payload = {
        "data": {
            "first_name": patient_name,
            "doctor_name": doctor_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time
        },
        "emailData": {
            "purpose": "EMAIL_APPOINTMENT_BOOKED_TEMPLATE",
            "to": "vivek@azodha.com",
            "subject": "Appointment Booked"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return "Email notification sent successfully!"
    except requests.exceptions.RequestException as e:
        return f"Failed to send email notification: {str(e)}"
def book_provider_appointment(provider_name, patient_name, appointment_time):
    tomorrow = dt.now() + timedelta(days=1)
    appointment_date = tomorrow.strftime(f"%Y-%m-%dT{appointment_time}:00.000Z")
    
    start_time_obj = dt.strptime(appointment_time, "%H:%M")
    end_time_obj = start_time_obj + timedelta(minutes=30)
    
    try:
        result = execute_tool(
            "book_appointment",
            patient_name=patient_name,
            doctor_name=provider_name,
            appointment_time=appointment_date,
            start_time=f"{appointment_time}:00",
            end_time=f"{end_time_obj.strftime('%H:%M')}:00",
            note="Regular checkup",
            event_title=f"Check-up Appointment for {patient_name}"
        )
        
        if "error" not in result.lower():
            email_result = send_appointment_email(patient_name, provider_name, appointment_date, appointment_time)
            return f"{result}\n\n{email_result}"
        
        return result
    except Exception as e:
        return f"Error booking appointment: {str(e)}"

@app.post("/api/chat/{session_id}")
async def chat(session_id: str, message: ChatMessage):
   try:
       user_message = message.content.lower().strip()
       response = {}
       
       if session_id not in sessions:
           sessions[session_id] = {
               "language": None,
               "current_question": 1,
               "survey_started": False,
               "survey_completed": False,
               "booking_stage": "not_started", 
               "selected_provider": None,
               "patient_name": None,
               "responses": {}
           }
       
       session = sessions[session_id]
       
       if session["language"] is None:
           if user_message in SUPPORTED_LANGUAGES:
               session["language"] = SUPPORTED_LANGUAGES[user_message]
               response = {
                   "message": "Language selected. Would you like to take our healthcare survey? (yes/no)"
               }
           else:
               response = {
                   "message": "Please select your language: English, Spanish (Español), Hindi (हिंदी), Chinese (中文), French (Français)"
               }
       
       elif not session["survey_started"]:
           if user_message in ["yes", "sí", "हाँ", "是", "oui"]:
               session["survey_started"] = True
               current_question = get_question_by_id(1)
               if current_question is None:
                   raise HTTPException(status_code=500, detail="Internal error: Question not found.")
               response = {"message": current_question["QuestionText"]}
           else:
               response = {"message": "Would you like to take our healthcare survey? (yes/no)"}
       
       elif session["survey_completed"]:
           if session["booking_stage"] == "selecting_provider":
               try:
                   provider_idx = int(user_message) - 1
                   if 0 <= provider_idx < len(PROVIDERS):
                       session["selected_provider"] = PROVIDERS[provider_idx]["name"]
                       session["booking_stage"] = "selecting_time"
                       response = {"message": "What time would you like to schedule for tomorrow? (HH:MM)"}
                   else:
                       raise ValueError()
               except ValueError:
                   response = {"message": "Invalid selection. Please choose a number 1-5."}
           
           elif session["booking_stage"] == "selecting_time":
               if validate_time_format(message.content):
                   booking_result = book_provider_appointment(
                       session["selected_provider"],
                       session["patient_name"],
                       message.content
                   )
                   session["booking_stage"] = "completed"
                   response = {"message": booking_result}
               else:
                   response = {"message": "Invalid time format. Please use HH:MM (e.g., 14:30)"}
       
       else:
           current_question = get_question_by_id(session["current_question"])
           if current_question is None:
               raise HTTPException(status_code=500, detail="Internal error: Question not found.")
           
           if validate_response(current_question, message.content, session["language"]):
               session["responses"][session["current_question"]] = message.content
               next_question_id = get_next_question_id(session["current_question"], message.content, session["language"])
               
               if next_question_id and next_question_id != 26:  # Not the last question
                   session["current_question"] = next_question_id
                   next_question = get_question_by_id(next_question_id)
                   response = {"message": next_question["QuestionText"]}
               else:  # Survey completed, start booking flow
                   session["survey_completed"] = True
                   session["booking_stage"] = "selecting_provider"
                   session["patient_name"] = "Arnav"  # Set default name
                   provider_list = "\n".join([f"{i+1}. {p['name']} - {p['specialty']}" 
                                        for i, p in enumerate(PROVIDERS)])
                   response = {"message": f"Survey completed successfully! Let's book your appointment.\n\nAvailable providers:\n{provider_list}\nPlease select (1-5):"}
           else:
               response = {"message": f"Invalid response. Please choose from: {current_question.get('Options', [])}"}

       # Send webhook
       webhook_payload = {
           "senderId": 5320,
           "receiverExternalId": 'a8ac5d00-3f77-4e59-9550-2cdae5c89e31',
           "message": response["message"]
       }
       
       webhook_url = "http://localhost:3000/api/webhook/ai-chatbot/listen/"
       headers = {
           "Content-Type": "application/json",
           "organization_code": "dev-demoorg",
           "api_key": "a29a99ac-383e-4ee9-bd76-3921b67b4c0c"
       }
       webhook_response = requests.post(webhook_url, json=webhook_payload, headers=headers)
       webhook_response.raise_for_status()
       
       return response

   except Exception as e:
       print(f"Error occurred: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
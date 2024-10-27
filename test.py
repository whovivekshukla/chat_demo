
import streamlit as st
from openai import OpenAI
import json
import time
import datetime
from survey_data import SURVEY_JSON
from tools import available_tools, execute_tool
from datetime import timedelta
from datetime import datetime as dt
import requests

# Initialize OpenAI client
client = OpenAI()

# Available providers list
PROVIDERS = [
    {"name": "Dr. Sarah Johnson", "specialty": "Primary Care"},
    {"name": "Dr. Michael Chen", "specialty": "Internal Medicine"},
    {"name": "Dr. Emily Williams", "specialty": "Family Medicine"},
    {"name": "Dr. James Rodriguez", "specialty": "General Practice"},
    {"name": "Dr. Lisa Anderson", "specialty": "Internal Medicine"}
]


def send_appointment_email(patient_name, doctor_name, appointment_date, appointment_time):
    """
    Send appointment confirmation email using the notification API
    """
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
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        return "Email notification sent successfully!"
    except requests.exceptions.RequestException as e:
        return f"Failed to send email notification: {str(e)}"


def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 3
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'survey_started' not in st.session_state:
        st.session_state.survey_started = False
    if 'survey_completed' not in st.session_state:
        st.session_state.survey_completed = False
    if 'booking_stage' not in st.session_state:
        st.session_state.booking_stage = "not_started"
    if 'selected_provider' not in st.session_state:
        st.session_state.selected_provider = None

def get_question_by_id(question_id):
    for question in SURVEY_JSON["Survey"]["Questions"]:
        if question["QuestionID"] == question_id:
            return question
    return None

def validate_response(question, response):
    system_prompt = """
    You are an AI assistant helping to validate survey responses. 
    Your task is to determine if a given response is valid for the question asked.
    Consider ranges in options, such as "5 to 9", and validate if the response falls within any specified range.
    When matching names, if only the first name is provided and it matches a single doctor, consider it valid. 
    However, if multiple doctors share the same first name, ensure the surname is also matched.
    Respond with only 'true' if the response is valid, or 'false' if it's invalid.
    """

    valid_options = question.get('Options', question.get('Scale', 'Any response'))
    print(f"Valid options: {valid_options}")
    print(f"User response: {response}")
    
    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {valid_options}
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
        st.error(f"Error validating response: {e}")
        return False

def interpret_response(question, response):
    system_prompt = """
    You are an AI assistant helping to interpret survey responses. 
    Your task is to map the given response to the closest valid option for the question.
    Respond with only the mapped option, or 'INVALID' if no mapping is possible.
    """

    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {question.get('Options', question.get('Scale', 'Any response'))}
    User response: {response}

    What is the interpreted response?
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
        st.error(f"Error interpreting response: {e}")
        return "INVALID"

def generate_ai_message(question, is_invalid=False, off_topic=False):
    system_prompt = """
    You are a healthcare survey assistant. Your goal is to:
    1. Ask survey questions directly and clearly
    2. Keep users focused on the survey
    3. Validate their responses
    4. Give brief acknowledgments
    5. If they go off-topic, redirect them to the survey
    
    Important guidelines:
    - Don't start with phrases like "I hope you're keeping well" or "I'd be happy to help"
    - Don't add unnecessary pleasantries
    - Go straight to the question
    - Keep responses concise
    - Maintain a professional tone
    - Don't add "I'm just curious" or similar phrases
    """

    if off_topic:
        prompt = f"""The user has gone off-topic. Politely acknowledge their comment and redirect them back to the current survey question:
        Current question: {question['QuestionText']}
        Options: {question.get('Options', question.get('Scale', ''))}
        """
    elif is_invalid:
        prompt = f"""The user provided an invalid response. Politely explain the valid options and ask the question again:
        Question: {question['QuestionText']}
        Valid options: {question.get('Options', question.get('Scale', ''))}
        """
    else:
        prompt = f"""Ask this survey question in a conversational way:
        Question: {question['QuestionText']}
        Options: {question.get('Options', question.get('Scale', ''))}
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content

def is_off_topic(user_input, current_question):
    system_prompt = """
    You are a survey assistant. Determine if the user's response is relevant to the current question.
    Return only "true" if the response is off-topic or "false" if it's a valid attempt to answer the question.
    """

    prompt = f"""
    Current question: {current_question['QuestionText']}
    Valid options: {current_question.get('Options', current_question.get('Scale', ''))}
    User response: {user_input}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content.lower() == "true"

def get_next_question_id(current_question_id, user_response):
    current_question = get_question_by_id(current_question_id)
    interpreted_response = interpret_response(current_question, user_response)
    
    if "SkipLogic" in current_question:
        next_question_id = current_question["SkipLogic"].get(interpreted_response)
        if next_question_id:
            return int(next_question_id[1:])  # Remove 'Q' prefix and convert to int
    
    questions = SURVEY_JSON["Survey"]["Questions"]
    current_index = next((i for i, q in enumerate(questions) if q["QuestionID"] == current_question_id), -1)
    if current_index < len(questions) - 1:
        return questions[current_index + 1]["QuestionID"]
    return None

def present_provider_options():
    provider_message = "Thank you for completing the survey! First, could you please tell me your name?"
    return provider_message

def validate_time_format(time_str):
    try:
        dt.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def book_provider_appointment(provider_name, patient_name, appointment_time):
    # Convert appointment time to required format
    tomorrow = dt.now() + timedelta(days=1)
    appointment_date = tomorrow.strftime(f"%Y-%m-%dT{appointment_time}:00.000Z")
    
    # Calculate end time (30 minutes after start time)
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
        
         # If booking successful, send email notification
        if "error" not in result.lower():
            email_result = send_appointment_email(patient_name, provider_name, appointment_date, appointment_time)
            return f"{result}\n\n{email_result}"
        
        return result
    except Exception as e:
        return f"Error booking appointment: {str(e)}"

def main():
    st.title("Healthcare Survey Assistant")
    
    initialize_session_state()

    # Initialize the survey if not started
    if not st.session_state.survey_started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm here to help you complete a healthcare survey. Would you like to start? (Please respond with 'Yes' to begin)"
        })
        st.session_state.survey_started = True

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Handle user input
    if user_input := st.chat_input("Your response"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Handle initial survey start
        if len(st.session_state.messages) <= 3 and user_input.lower() == "yes":
            initial_question = generate_ai_message(get_question_by_id(1))
            st.session_state.messages.append({"role": "assistant", "content": initial_question})
            st.session_state.current_question = 1
        
        # Handle provider selection and booking
        elif st.session_state.survey_completed:
            if st.session_state.booking_stage == "not_started":
                # Collect patient name
                st.session_state.patient_name = user_input
                provider_list = "Here are our available providers:\n\n"
                for i, provider in enumerate(PROVIDERS, 1):
                    provider_list += f"{i}. {provider['name']} - {provider['specialty']}\n"
                provider_list += "\nPlease enter the number of the provider you'd like to schedule with (1-5):"
                st.session_state.messages.append({"role": "assistant", "content": provider_list})
                st.session_state.booking_stage = "selecting_provider"

            # Replace the provider selection section in the main() function with this:
            elif st.session_state.booking_stage == "selecting_provider":
                provider_question = {
                    "QuestionID": "provider_selection",
                    "QuestionText": "Please select your preferred healthcare provider",
                    "Options": [provider['name'] for provider in PROVIDERS]  # Just array of names: ["Dr. Sarah Johnson", "Dr. Michael Chen", etc.]
                }
                
                is_valid = validate_response(provider_question, user_input)
                if is_valid:
                    interpreted_response = interpret_response(provider_question, user_input)
                    for i, provider in enumerate(PROVIDERS):
                        if provider["name"] in interpreted_response or str(i + 1) in interpreted_response:
                            st.session_state.selected_provider = provider["name"]
                            time_request = "What time would you like to schedule your appointment for tomorrow? Please use 24-hour format (HH:MM), e.g., 14:30 for 2:30 PM:"
                            st.session_state.messages.append({"role": "assistant", "content": time_request})
                            st.session_state.booking_stage = "selecting_time"
                            break
                    else:  # This runs if no break occurred in the for loop
                        provider_list = "I couldn't understand your selection. Here are our available providers:\n\n"
                        for i, provider in enumerate(PROVIDERS, 1):
                            provider_list += f"{i}. {provider['name']} - {provider['specialty']}\n"
                        provider_list += "\nPlease enter the number of the provider you'd like to schedule with (1-5):"
                        st.session_state.messages.append({"role": "assistant", "content": provider_list})
                else:
                    provider_list = "I couldn't understand your selection. Here are our available providers:\n\n"
                    for i, provider in enumerate(PROVIDERS, 1):
                        provider_list += f"{i}. {provider['name']} - {provider['specialty']}\n"
                    provider_list += "\nPlease enter the number of the provider you'd like to schedule with (1-5):"
                    st.session_state.messages.append({"role": "assistant", "content": provider_list})

            elif st.session_state.booking_stage == "selecting_time":
                if validate_time_format(user_input):
                    booking_result = book_provider_appointment(
                        st.session_state.selected_provider,
                        st.session_state.patient_name,
                        user_input
                    )
                    st.session_state.messages.append({"role": "assistant", "content": booking_result})
                    st.session_state.booking_stage = "completed"
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Please enter a valid time in 24-hour format (HH:MM), e.g., 14:30 for 2:30 PM:"
                    })
        
        # Handle ongoing survey
        else:
            current_question = get_question_by_id(st.session_state.current_question)
            is_valid = validate_response(current_question, user_input)
            
            if is_valid:
                interpreted_response = interpret_response(current_question, user_input)
                st.session_state.responses[current_question["QuestionID"]] = interpreted_response
                
                next_question_id = get_next_question_id(st.session_state.current_question, user_input)
                next_question = get_question_by_id(next_question_id)
                
                if next_question:
                    st.session_state.current_question = next_question_id
                    response = generate_ai_message(next_question)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    # Survey complete, begin booking process
                    st.session_state.survey_completed = True
                    provider_options = present_provider_options()
                    st.session_state.messages.append({"role": "assistant", "content": provider_options})
                    st.session_state.booking_stage = "not_started"
            else:
                response = generate_ai_message(current_question, is_invalid=True)
                st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

if __name__ == "__main__":
    main()



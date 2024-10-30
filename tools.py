from typing import Callable, Dict, Any
from datetime import datetime
import requests
import json
from pydantic import BaseModel

class BookAppointmentInput(BaseModel):
    patient_name: str
    doctor_name: str
    appointment_time: str
    appointment_type_id: int = 3720  # default value
    start_time: str
    end_time: str
    duration_in_minutes: int = 30  # default value
    note: str
    event_title: str
    status: str = "SCHEDULED"  # default value
    booking_category: str = "Event"  # default value
    override_slots: bool = True  # default value

def get_current_time(**kwargs) -> str:
    """Get the current time"""
    return datetime.now().strftime("%H:%M:%S")

def book_appointment(
    patient_name: str,
    doctor_name: str,
    appointment_time: str,
    start_time: str,
    end_time: str,
    note: str,
    event_title: str,
    appointment_type_id: int = 3720,
    duration_in_minutes: int = 30,
    status: str = "SCHEDULED",
    booking_category: str = "Event",
    override_slots: bool = True
) -> str:
    """Make a POST request to book an appointment. and when done ask user if they have received the appointment confirmation on email"""
    
    url = "https://platform-api-development.azo.dev/api/service-provider-scheduling/appointments"
    payload = {
        "appointmentTypeId": appointment_type_id,
        "date": appointment_time,
        "startTime": start_time,
        "endTime": end_time,
        "overrideSlots": override_slots,
        "durationInMinutes": duration_in_minutes,
        "patientId": "e9ba687a25ae4c3cb7dd",
        "attributes": {
            "eventTitle": event_title,
            "status": status,
            "bookingCategory": booking_category,
            "overrideSlots": override_slots
        }
    }
    headers = {
        'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InFWMDZzQzkzVS1UNWRIdXhRSWY1TyJ9.eyJuaWNrbmFtZSI6ImFybmF2K2NhcmUydSIsIm5hbWUiOiJhcm5hditjYXJlMnVAYXpvZGhhLmNvbSIsInBpY3R1cmUiOiJodHRwczovL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9iNTRmYzQ3YTIyNjRmODk1NTExMzIzMmExMGYxNjE5NT9zPTQ4MCZyPXBnJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJGYXZhdGFycyUyRmFyLnBuZyIsInVwZGF0ZWRfYXQiOiIyMDI0LTEwLTMwVDE1OjQ5OjM4LjM3OFoiLCJlbWFpbCI6ImFybmF2K2NhcmUydUBhem9kaGEuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJpc3MiOiJodHRwczovL2Rldi1jYXJlMnUudXMuYXV0aDAuY29tLyIsImF1ZCI6ImdVNzhLaTNDRmVzaUZHYlR6ZUR6RHpCTDE5MDFobkhWIiwiaWF0IjoxNzMwMzAzMzgwLCJleHAiOjE3MzAzMzkzODAsInN1YiI6ImF1dGgwfDY3MTM4MTAwNGU4YTg5MDdmYmYwYzBmMCIsInNpZCI6InczMnJLZ1UwLVNQT0lzblZoeVduNV9teXhLSlVxanAtIiwibm9uY2UiOiJRbHBJYzE5eFpGbG9iV1JOVDJ4d2R6TTRhR3R2TUVnMlVHVXRWbkpEVm1ZdWNUVnRlR294TlVwcWF3PT0ifQ.yhZo-tsk51SzRqk34Ub5C3LRN5voj9xZdRjboYCV9mepC3ye_TmTb867bPRQxMvm2LhgTm52yqhkeDLxC6OUxpx05XgMpm3jAe_IcZadREpywXwMxEFAKczfLecZH3zXR1EDUYBD4DWFEUjspl1Z77Tm9E3-2GVc_wuSepfKugAutO0IaT3Acl5urRxwxa0KodWamwSuVoAEtzVWE437Hj3iRXxC47c5A1IWDnl1d96v6xzaIEGvUgQqw6mvadoYoAQxY3nVxSqz_u5m7iS-ASKvj8yzaSWK0sz8vVAhRSu1p8sou-HxF_pGQ3YaBNvLwUHLy2y-CbPZofw94Q_EeQ',
        'organization_code': 'dev-care2u',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            return "Appointment successfully booked! Please check your email for confirmation."
        else:
            return f"Failed to book appointment. Status code: {response.status_code}"
    except Exception as e:
        return f"Error booking appointment: {str(e)}"

# Array of available tools with their schemas
available_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a medical appointment through the API",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {
                        "type": "string",
                        "description": "Name of the patient"
                    },
                    "doctor_name": {
                        "type": "string",
                        "description": "Name of the doctor"
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Date of the appointment in ISO format (YYYY-MM-DDTHH:mm:ss.sssZ)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time of the appointment (HH:mm:ss)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time of the appointment (HH:mm:ss)"
                    },
                    "note": {
                        "type": "string",
                        "description": "Additional notes for the appointment"
                    },
                    "event_title": {
                        "type": "string",
                        "description": "Title of the appointment"
                    },
                    "appointment_type_id": {
                        "type": "integer",
                        "description": "Type ID of the appointment",
                        "default": 3720
                    },
                    "duration_in_minutes": {
                        "type": "integer",
                        "description": "Duration of the appointment in minutes",
                        "default": 30
                    },
                    "status": {
                        "type": "string",
                        "description": "Status of the appointment",
                        "default": "SCHEDULED"
                    },
                    "booking_category": {
                        "type": "string",
                        "description": "Category of the booking",
                        "default": "Event"
                    },
                    "override_slots": {
                        "type": "boolean",
                        "description": "Whether to override time slots",
                        "default": "true"
                    }
                },
                "required": [
                    "patient_name",
                    "doctor_name",
                    "appointment_time",
                    "start_time",
                    "end_time",
                    "note",
                    "event_title"
                ]
            }
        }
    }
]

# Dictionary mapping function names to their implementations
tool_functions = {
    "get_current_time": get_current_time,
    "book_appointment": book_appointment
}

def execute_tool(tool_name: str, **kwargs) -> Any:
    """Execute a tool by name with given arguments"""
    if tool_name not in tool_functions:
        raise ValueError(f"Tool {tool_name} not found")
    return tool_functions[tool_name](**kwargs)
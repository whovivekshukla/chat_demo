SURVEY_JSON = {
    "Survey": {
        "Title": "CAHPS Health Plan Survey Adult Medicaid Survey 5.1",
        "Version": "5.1",
        "Language": "English",
        "Questions": [
            {
                "QuestionID": 1,
                "QuestionText": "In the last 6 months, did you have an illness, injury, or condition that needed care right away?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q2", "No": "Q3"}
            },
            {
                "QuestionID": 2,
                "QuestionText": "In the last 6 months, when you needed care right away, how often did you get care as soon as you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 3,
                "QuestionText": "In the last 6 months, did you make any in-person, phone, or video appointments for a check-up or routine care?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q4", "No": "Q5"}
            },
            {
                "QuestionID": 4,
                "QuestionText": "In the last 6 months, how often did you get an appointment for a check-up or routine care as soon as you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 5,
                "QuestionText": "In the last 6 months, not counting the times you went to an emergency room, how many times did you get health care for yourself in person, by phone, or by video?",
                "Options": ["None", "1 time", "2", "3", "4", "5 to 9", "10 or more"]
            },
            {
                "QuestionID": 6,
                "QuestionText": "Using any number from 0 to 10, where 0 is the worst health care possible and 10 is the best health care possible, what number would you use to rate all your health care in the last 6 months?",
                "Scale": {"Min": 0, "Max": 10}
            },
            {
                "QuestionID": 7,
                "QuestionText": "In the last 6 months, how often was it easy to get the care, tests, or treatment you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 8,
                "QuestionText": "Do you have a personal doctor?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q9", "No": "Q12"}
            }
        ]
    }
}
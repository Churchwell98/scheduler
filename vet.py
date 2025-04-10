'''
vet.py
Contains functions to input VET (Voluntary Extra Time)
'''

from datetime import datetime, timedelta

# Constants
FILENAME = "schedule.json"
DEFAULT_WORK_DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"]
DEFAULT_SHIFT = {"type": "WORK", "start_time": "03:00 AM", "end_time": "11:30 AM"}

def input_vet(schedule):
    """Input VET for a specific date."""
    # Get the current date
    current_date = datetime.today().strftime("%m/%d/%Y")
    
    # Ask the user for the date they want to input VET
    input_date = input("Enter the date for VET (MM/DD/YYYY): ")

    # Check if the input date is in the past
    if datetime.strptime(input_date, "%m/%d/%Y") < datetime.strptime(current_date, "%m/%d/%Y"):
        print(f"Error: {input_date} is in the past. Cannot input VET for past dates.")
        return schedule  # Return the schedule unchanged
    
    # Check if the input date is beyond the current week
    today = datetime.today()
    days_until_saturday = (5 - today.weekday()) % 7  # Saturday = 5
    end_of_week = today + timedelta(days=days_until_saturday)
    
    if datetime.strptime(input_date, "%m/%d/%Y") > end_of_week:
        print(f"Error: {input_date} is beyond the current week. Please input VET closer to the date.")#Or else this will break the optimization logic
        return schedule

    # Fill in any missing days in between
    schedule_dates = [datetime.strptime(date, "%m/%d/%Y") for date in schedule.keys()]
    if schedule_dates:
        last_date_in_schedule = max(schedule_dates)
    else:
        last_date_in_schedule = datetime.strptime("01/01/2000", "%m/%d/%Y")

    input_date_obj = datetime.strptime(input_date, "%m/%d/%Y")
    if input_date_obj > last_date_in_schedule:
        # Fill in the missing days
        current_day = last_date_in_schedule + timedelta(days=1)
        while current_day <= input_date_obj:
            date_str = current_day.strftime("%m/%d/%Y")
            weekday = current_day.strftime("%A")
            if weekday in DEFAULT_WORK_DAYS:
                schedule[date_str] = [DEFAULT_SHIFT.copy()]
            else:
                schedule[date_str] = []
            current_day += timedelta(days=1)

    if input_date not in schedule:
        schedule[input_date] = []  # Initialize if the date doesn't exist

    # Ask for VET start and end times
    vet_start_time = input("Enter VET start time (HH:MM AM/PM): ")
    vet_end_time = input("Enter VET end time (HH:MM AM/PM): ")

    vet_start = datetime.strptime(vet_start_time, "%I:%M %p")
    vet_end = datetime.strptime(vet_end_time, "%I:%M %p")

    # Merge VET with existing shifts if they touch or overlap
    new_shifts = []
    merged = False

    for shift in schedule[input_date]:
        shift_start = datetime.strptime(shift['start_time'], "%I:%M %p")
        shift_end = datetime.strptime(shift['end_time'], "%I:%M %p")

        if (vet_start <= shift_end and vet_end >= shift_start):
            # Overlaps or directly touches, merge into one shift
            merged_start = min(shift_start, vet_start)
            merged_end = max(shift_end, vet_end)
            new_shifts.append({
                "type": "WORK",
                "start_time": merged_start.strftime("%I:%M %p"),
                "end_time": merged_end.strftime("%I:%M %p")
            })
            merged = True
        else:
            # No overlap, keep the existing shift
            new_shifts.append(shift)

    if not merged:
        # VET did not overlap with any existing shift, so add it as its own shift
        new_shifts.append({
            "type": "WORK",
            "start_time": vet_start.strftime("%I:%M %p"),
            "end_time": vet_end.strftime("%I:%M %p")
        })

    # Replace the day's schedule with the updated shifts (including any merged VET)
    schedule[input_date] = new_shifts

    print(f"VET applied from {vet_start_time} to {vet_end_time} on {input_date}.")
    return schedule
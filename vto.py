'''
vto.py
Contains functions to input VTO
'''

from datetime import datetime, timedelta

# Constants
FILENAME = "schedule.json"
DEFAULT_WORK_DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"]
DEFAULT_SHIFT = {"type": "WORK", "start_time": "03:00 AM", "end_time": "11:30 AM"}

def input_vto(schedule):
    """Input VTO for a specific date."""
    # Get the current date
    current_date = datetime.today().strftime("%m/%d/%Y")
    
    # Ask the user for the date they want to input VTO
    input_date = input("Enter the date for VTO (MM/DD/YYYY): ")

    # Check if the input date is in the past
    if datetime.strptime(input_date, "%m/%d/%Y") < datetime.strptime(current_date, "%m/%d/%Y"):
        print(f"Error: {input_date} is in the past. Cannot input VTO for past dates.")
        return schedule  # Return the schedule unchanged
    
    # Check if the input date is beyond the current week
    today = datetime.today()
    days_until_saturday = (5 - today.weekday()) % 7  # Saturday = 5
    end_of_week = today + timedelta(days=days_until_saturday)
    
    if datetime.strptime(input_date, "%m/%d/%Y") > end_of_week:
        print(f"Error: {input_date} is beyond the current week. Please input VTO closer to the date.")#Or else this will break the optimization logic
        return schedule

    # Fill in any missing days in between
    # Get the last date in the current schedule
    schedule_dates = [datetime.strptime(date, "%m/%d/%Y") for date in schedule.keys()]
    if schedule_dates:
        last_date_in_schedule = max(schedule_dates)
    else:
        last_date_in_schedule = datetime.strptime("01/01/2000", "%m/%d/%Y")  # Arbitrary start date if schedule is empty

    # If the input date is after the last date in the schedule, add missing days
    input_date_obj = datetime.strptime(input_date, "%m/%d/%Y")
    if input_date_obj > last_date_in_schedule:
        # Fill in the missing days
        current_day = last_date_in_schedule + timedelta(days=1)
        while current_day <= input_date_obj:
            date_str = current_day.strftime("%m/%d/%Y")
            weekday = current_day.strftime("%A")
            # Add missing day with the default work shift if it's a work day
            if weekday in DEFAULT_WORK_DAYS:
                schedule[date_str] = [DEFAULT_SHIFT.copy()]
            else:
                schedule[date_str] = []
            current_day += timedelta(days=1)

    # Now handle the input VTO logic
    if input_date not in schedule:
        schedule[input_date] = []  # Add the date to the schedule if it doesn't exist
    
    # Ask the user if the VTO is for a full or partial shift
    vto_type = input("Is this a full shift (y/n)? ").lower()
    if vto_type == 'y':
        # Remove the entire shift for that day
        schedule[input_date] = []
        print(f"Full shift VTO applied for {input_date}.")
    else:
        # For partial shift, ask for the VTO start and end time
        start_time = input("Enter VTO start time (HH:MM AM/PM): ")
        end_time = input("Enter VTO end time (HH:MM AM/PM): ")

        # Adjust the shifts accordingly
        shifts_for_day = schedule.get(input_date, [])
        for shift in shifts_for_day:
            # If the VTO time falls within the shift, adjust the shift timing
            shift_start = datetime.strptime(shift['start_time'], "%I:%M %p")
            shift_end = datetime.strptime(shift['end_time'], "%I:%M %p")
            vto_start = datetime.strptime(start_time, "%I:%M %p")
            vto_end = datetime.strptime(end_time, "%I:%M %p")

            # Remove VTO time from the shift if it's within the shift's time
            if vto_start >= shift_start and vto_end <= shift_end:
                if vto_start > shift_start:
                    # Keep the portion before VTO
                    schedule[input_date] = [{
                        "type": shift["type"],
                        "start_time": shift["start_time"],
                        "end_time": start_time
                    }]
                if vto_end < shift_end:
                    # Keep the portion after VTO
                    schedule[input_date].append({
                        "type": shift["type"],
                        "start_time": end_time,
                        "end_time": shift["end_time"]
                    })
                print(f"Partial VTO applied from {start_time} to {end_time} on {input_date}.")
                break
        else:
            print("Error: No shift found on the selected date.")

    return schedule
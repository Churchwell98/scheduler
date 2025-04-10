'''
schedule.py
Handles schedule loading, saving, and cleaning.
'''

import json
import os
from datetime import datetime, timedelta
import re
from collections import defaultdict, deque

# Constants
FILENAME = "schedule.json"
DEFAULT_WORK_DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"]
DEFAULT_SHIFT = {"type": "WORK", "start_time": "03:00 AM", "end_time": "11:30 AM"}
PREP_TIME = timedelta(minutes=45)
COMMUTE_TIME = timedelta(minutes=15)

#Functions
def convert_to_datetime(time_str):
    # Handle the special case where '00:00 AM' should be '12:00 AM'
    if time_str == '00:00 AM':
        time_str = '12:00 AM'
    
    return datetime.strptime(time_str, '%I:%M %p')

def format_time(dt):
    return dt.strftime("%I:%M %p").replace("00:", "12:")

def get_current_week():
    """Get a dictionary with the current week's days, including default work shifts."""
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Get Monday of current week
    start_of_week -= timedelta(days=1)  # Adjust to start from Sunday
    week_schedule = {}

    for i in range(7):
        date_obj = start_of_week + timedelta(days=i)
        day_label = date_obj.strftime("%m/%d/%Y")  # Now using only date format
        week_schedule[day_label] = [DEFAULT_SHIFT.copy()] if date_obj.strftime("%A") in DEFAULT_WORK_DAYS else []

    return week_schedule

def load_schedule():
    """Load schedule from file, or create a new one if missing."""
    if not os.path.exists(FILENAME):
        print("No schedule file found. Creating a new one with default work schedule...")
        schedule = get_current_week()
        save_schedule(schedule)
    else:
        with open(FILENAME, "r") as file:
            schedule = json.load(file)
        schedule = clean_old_days(schedule)
    return schedule

def save_schedule(schedule):
    """Save schedule to file."""
    with open(FILENAME, "w") as file:
        json.dump(schedule, file, indent=4)

def clean_old_days(schedule):
    """Remove outdated days and add missing workdays."""
    current_week = get_current_week()
    
    # Keep only relevant days and ensure work shifts are present
    updated_schedule = {day: schedule.get(day, current_week[day]) for day in current_week}

    # Add missing default work shifts
    for day in current_week:
        weekday = day.split(",")[0]  # Extract just the weekday name
        if weekday in DEFAULT_WORK_DAYS and not any(shift["type"] == "WORK" for shift in updated_schedule[day]):
            updated_schedule[day].append(DEFAULT_SHIFT.copy())

    save_schedule(updated_schedule)
    return updated_schedule

def display_schedule(schedule):
    """Display the schedule with both the day of the week and the date."""
    print("\nWeekly Schedule:")
    for day, shifts in schedule.items():
        # Get the weekday name (e.g., Saturday) and format it with the date
        day_of_week = datetime.strptime(day, "%m/%d/%Y").strftime("%A")
        print(f"\n{day_of_week}, {day}:")  # Display day of week and date
        if shifts:
            for shift in shifts:
                print(f"  {shift['type']}: {shift['start_time']} - {shift['end_time']}")
        else:
            print("  No shifts scheduled.")

def clean_schedule(schedule):
    """Remove all non-WORK shifts from today onward."""
    today = datetime.today().strftime("%m/%d/%Y")
    cleaned_schedule = {}

    for day, shifts in schedule.items():
        if day >= today:  # Only clean days from today forward
            cleaned_schedule[day] = [shift for shift in shifts if shift["type"] == "WORK"]
        else:
            # Keep past days unchanged
            cleaned_schedule[day] = shifts

    return cleaned_schedule

def optimize_schedule(schedule):
    '''
    Possible shift types: WORK, MEAL, SLEEP, COMMUTE, JOB SEARCH, SHOWER, PREP
    '''
    schedule=optimize_sleep(schedule)
    schedule=optimize_search(schedule)

    return schedule

def optimize_sleep(schedule):#Assign mandatory shifts and sleep
    '''
    schedule is a dictionary with dates as keys, and lists of dictionaries as values
    '''
    today = datetime.today().strftime("%m/%d/%Y")#Get current day

    for i, (date,shifts) in enumerate(schedule.items()):#Iterate over each day in schedule

        if date<today:#If day is in the past
            continue#Skip optimiztion, move on to next day

        if any(shift['type'] == 'WORK' for shift in shifts):#A work day
            #print(f"{date} is a work day")

            # Extract work shifts
            work_shifts = [shift for shift in shifts if shift['type'] == 'WORK']

            if len(work_shifts) == 1:  # Only one work shift
                print(f"  One work shift on {date}")
                
                # Extract work shift details (only one work shift)
                work_shift = work_shifts[0]
                work_start = work_shift['start_time']
                work_end = work_shift['end_time']
                
                # Calculate the sleep shift (only if the previous day wasn't a work day)
                if i == 0 or not any(shift['type'] == 'WORK' for shift in schedule[list(schedule.keys())[i - 1]]):
                    sleep_start = calculate_nap_start(work_start)  # Custom function to calculate sleep time
                    sleep_end = add_duration(sleep_start, 2)  # 2-hour nap
                    shifts.insert(0, {'type': 'SLEEP', 'start_time': sleep_start, 'end_time': sleep_end})

                # Schedule PREP, COMMUTE, MEAL, SHOWER, and the second SLEEP shift
                prep_start = add_duration(work_start, -1)  # 1 hour before work
                prep_end = add_duration(prep_start, 0.75)  # 45-minute duration

                commute_to_start = add_duration(work_start, -0.25)  # 15 minutes before work
                commute_to_end = add_duration(commute_to_start, 0.25)  # 15-minute commute

                commute_from_start = work_end
                commute_from_end = add_duration(commute_from_start, 0.25)  # 15-minute commute

                meal_start = commute_from_end
                meal_end = add_duration(meal_start, 1)  # 1-hour meal

                shower_start = meal_end
                shower_end = add_duration(shower_start, 1)  # 1-hour shower

                # Post-work sleep logic
                # Check if the next day is a work day
                next_day = list(schedule.keys())[i + 1] if i + 1 < len(schedule) else None
                next_day_work = any(shift['type'] == 'WORK' for shift in schedule.get(next_day, []))

                if next_day_work:  # Next day is a work day
                    second_sleep_start = max(shower_end, '3:00 PM')  # Start after shower, or at 3 PM if later
                    second_sleep_end = add_duration(second_sleep_start, 8)  # 8-hour sleep duration
                else:  # Next day is not a work day
                    second_sleep_start = shower_end  # Start immediately after the shower
                    second_sleep_end = '6:30 PM'  # End at 6:30 PM

                #Post-sleep meal
                second_meal_start = second_sleep_end
                second_meal_end = add_duration(second_meal_start, 1)  # 1-hour meal
                if second_meal_start[:2]=='11' and second_meal_start[-2:]=='PM':#Handles going into next day
                    second_meal_end=second_meal_end[:-2]+'AM'
                    print(second_meal_end)

                shifts.extend([
                    {'type': 'PREP', 'start_time': prep_start, 'end_time': prep_end},
                    {'type': 'COMMUTE', 'start_time': commute_to_start, 'end_time': commute_to_end},
                ])

                # Only add WORK if it's not already in shifts
                if not any(shift['type'] == 'WORK' and shift['start_time'] == work_start for shift in shifts):
                    shifts.append({'type': 'WORK', 'start_time': work_start, 'end_time': work_end})

                shifts.extend([
                    {'type': 'COMMUTE', 'start_time': commute_from_start, 'end_time': commute_from_end},
                    {'type': 'MEAL', 'start_time': meal_start, 'end_time': meal_end},
                    {'type': 'SHOWER', 'start_time': shower_start, 'end_time': shower_end},
                    {'type': 'SLEEP', 'start_time': second_sleep_start, 'end_time': second_sleep_end},
                    {'type': 'MEAL', 'start_time': second_meal_start, 'end_time': second_meal_end},
                ])

            elif len(work_shifts) > 1:  # Multiple work shifts
                print(f"  Multiple work shifts on {date}")

                # Get the start time of the first work shift and the end time of the last work shift
                first_work_start = work_shifts[0]['start_time']
                last_work_end = work_shifts[-1]['end_time']
                
                # Calculate the optional nap before the first work shift (if needed)
                if i == 0 or not any(shift['type'] == 'WORK' for shift in schedule[list(schedule.keys())[i - 1]]):
                    nap_start = calculate_nap_start(first_work_start)  # Calculate nap time
                    nap_end = add_duration(nap_start, 2)  # 2-hour nap
                    shifts.insert(0, {'type': 'SLEEP', 'start_time': nap_start, 'end_time': nap_end})

                # Schedule PREP, COMMUTE for the first work shift (based on the first work shift's start time)
                prep_start = add_duration(first_work_start, -1)  # 1 hour before the first work shift
                prep_end = add_duration(prep_start, 0.75)  # 45-minute duration

                commute_to_start = add_duration(first_work_start, -0.25)  # 15 minutes before the first work shift
                commute_to_end = add_duration(commute_to_start, 0.25)  # 15-minute commute

                shifts.insert(0, {'type': 'PREP', 'start_time': prep_start, 'end_time': prep_end})
                shifts.insert(1, {'type': 'COMMUTE', 'start_time': commute_to_start, 'end_time': commute_to_end})

                # Schedule WORK shifts (already in the schedule)

                # Commute after the last work shift and subsequent shifts (MEAL, SHOWER, SLEEP)
                commute_from_start = last_work_end
                commute_from_end = add_duration(commute_from_start, 0.25)  # 15-minute commute

                meal_start = commute_from_end
                meal_end = add_duration(meal_start, 1)  # 1-hour meal

                shower_start = meal_end
                shower_end = add_duration(shower_start, 1)  # 1-hour shower

                # Post-work sleep logic
                # Check if the next day is a work day
                next_day = list(schedule.keys())[i + 1] if i + 1 < len(schedule) else None
                next_day_work = any(shift['type'] == 'WORK' for shift in schedule.get(next_day, []))

                if next_day_work:  # Next day is a work day
                    second_sleep_start = max(shower_end, '3:00 PM')  # Start after shower, or at 3 PM if later
                    second_sleep_end = add_duration(second_sleep_start, 8)  # 8-hour sleep duration
                else:  # Next day is not a work day
                    second_sleep_start = shower_end  # Start immediately after the shower
                    second_sleep_end = '6:30 PM'  # End at 6:30 PM

                #Post-sleep meal
                second_meal_start = second_sleep_end
                second_meal_end = add_duration(second_meal_start, 1)  # 1-hour meal
                if second_meal_start[:2]=='11' and second_meal_start[-2:]=='PM':#Handles going into next day
                    second_meal_end=second_meal_end[:-2]+'AM'

                shifts.extend([
                    {'type': 'COMMUTE', 'start_time': commute_from_start, 'end_time': commute_from_end},
                    {'type': 'MEAL', 'start_time': meal_start, 'end_time': meal_end},
                    {'type': 'SHOWER', 'start_time': shower_start, 'end_time': shower_end},
                    {'type': 'SLEEP', 'start_time': second_sleep_start, 'end_time': second_sleep_end},
                    {'type': 'MEAL', 'start_time': second_meal_start, 'end_time': second_meal_end},
                ])

        else:#Not a work day
            #print(f"{date} is not a work day")

            # Define the fixed schedule for non-work days
            sleep_start = "2:00 AM"
            sleep_end = "10:00 AM"
            
            meal_breakfast_start = "10:00 AM"
            meal_breakfast_end = "10:30 AM"
            
            meal_lunch_start = "1:00 PM"
            meal_lunch_end = "2:00 PM"
            
            meal_dinner_start = "7:00 PM"
            meal_dinner_end = "8:00 PM"
            
            shower_start = "8:00 PM"
            shower_end = "9:00 PM"
            
            # Add the shifts for non-work day
            shifts.extend([
                {'type': 'SLEEP', 'start_time': sleep_start, 'end_time': sleep_end},
                {'type': 'MEAL', 'start_time': meal_breakfast_start, 'end_time': meal_breakfast_end},
                {'type': 'MEAL', 'start_time': meal_lunch_start, 'end_time': meal_lunch_end},
                {'type': 'MEAL', 'start_time': meal_dinner_start, 'end_time': meal_dinner_end},
                {'type': 'SHOWER', 'start_time': shower_start, 'end_time': shower_end},
            ])

        # After inserting all shifts for a given date, sort them by start_time
        for date, shifts in schedule.items():
            shifts.sort(key=lambda x: convert_to_datetime(x['start_time']))

    return schedule

def calculate_nap_start(work_start):#Calculates start time for optional nap
    # Custom logic to calculate sleep start time 3 hours before work start
    # This assumes work_start is in 12-hour format (e.g., '03:00 AM')
    work_hour, work_minute = int(work_start[:2]), int(work_start[3:5])
    sleep_hour = work_hour - 3
    sleep_minute = work_minute
    return f'{sleep_hour % 12:02d}:{sleep_minute:02d} {"AM" if sleep_hour < 12 else "PM"}'

def add_duration(start_time, duration):
    # This function adds the given duration (in hours, including fractional hours) to the start time.
    
    # Clean the start time (remove any leading/trailing spaces)
    start_time = start_time.strip()

    # Use regex to extract hour, minute, and AM/PM from the time string
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', start_time)
    
    if not match:
        raise ValueError(f"Invalid time format: {start_time}")
    
    start_hour = int(match.group(1))
    start_minute = int(match.group(2))
    start_period = match.group(3).upper()

    # Convert the start time to 24-hour format
    if start_period == "PM" and start_hour != 12:
        start_hour += 12
    elif start_period == "AM" and start_hour == 12:
        start_hour = 0
    
    # Convert the duration (which is a float) to hours and minutes
    hours_to_add = int(duration)
    minutes_to_add = round((duration - hours_to_add) * 60)

    # Add the hours and minutes to the start time
    total_minutes = (start_hour * 60 + start_minute) + (hours_to_add * 60 + minutes_to_add)
    
    # Calculate the new hour and minute
    total_hour = total_minutes // 60
    total_minute = total_minutes % 60

    # Determine AM/PM for the new time
    period = "AM" if total_hour < 12 else "PM"
    
    # Convert to 12-hour format
    total_hour = total_hour % 12
    if total_hour == 0:
        total_hour = 12  # Handle 12 AM/PM case
    
    # Format the output correctly
    return f'{total_hour:02}:{total_minute:02} {period}'

def optimize_search(schedule):#Optimize job search time
    """
    Assigns job search time (up to 40 hours per week) in 30-minute blocks while balancing time across days.
    Merges consecutive job search blocks into longer sessions.
    Ensures sleep is not reduced below 6.5 hours.
    Only allocates job search time starting from today.
    Considers job search time already allocated since the beginning of the week.
    schedule is a dictionary with dates as keys, and lists of dictionaries as values
    WORKS
    """
    job_search_goal = 40 * 60  # 40 hours in minutes
    job_search_block = 30  # 30-minute intervals
    min_sleep = 6.5 * 60  # Minimum sleep in minutes
    
    #Determine Remaining job search hours
    '''
    The goal is to dedicate 40 hours per week for job search
    Some time might already have been dedicated earlier in the week, so the remaining time might be less than 40 hours.
    The week always starts on Sunday
    '''
    today = datetime.today().strftime("%m/%d/%Y")#Get current day
    today_dt = datetime.strptime(today, "%m/%d/%Y")
    
    # Find the start of the week (Sunday)
    week_start = today_dt - timedelta(days=today_dt.weekday() + 1)  # Sunday of the current week
    week_start_str = week_start.strftime("%m/%d/%Y")
    
    # Track job search time already allocated
    total_job_search_allocated = 0

    for date in schedule:
        if date >= week_start_str and date < today:  # Look at past days in the current week
            for event in schedule[date]:
                if event["type"] == "JOB_SEARCH":
                    #start_time = datetime.strptime(event["start_time"], "%I:%M %p")
                    #end_time = datetime.strptime(event["end_time"], "%I:%M %p")
                    start_time = convert_to_datetime(event["start_time"])
                    end_time = convert_to_datetime(event["end_time"])
                    total_job_search_allocated += (end_time - start_time).seconds // 60  # Convert to minutes
    
    remaining_job_search_time = max(0, job_search_goal - total_job_search_allocated)

    #print(f"Total job search already allocated: {total_job_search_allocated} minutes")
    #print(f"Remaining job search time to assign: {remaining_job_search_time} minutes")

    # If no more job search time is needed, return the schedule as is
    if remaining_job_search_time == 0:
        return schedule
    
    # First pass: Assign job search time into available blocks
    '''
    Assign job search time in 30 minute intervals into any unoccupied time slots
    Start from the current day
    Balance it out between each day as much as possible.
    Merge any adjacent blocks of job search time into one.
    If there are multiple WORK shifts, DO NOT assign job search time in between them (I can only do job search time at home)
    Make sure all blocks of time are ordered consecutively
    Do not overlap into the next day
    '''
    # Step 1: Collect available blocks across all days starting from today
    all_available_blocks = []
    for date in sorted(schedule.keys()):
        if date < today:
            continue

        busy_intervals = []
        for event in schedule[date]:
            start_time = convert_to_datetime(event["start_time"])
            end_time = convert_to_datetime(event["end_time"])
            busy_intervals.append((start_time, end_time))
        busy_intervals.sort()

        available_blocks = []
        last_end_time = convert_to_datetime("12:00 AM")
        for start, end in busy_intervals:
            if last_end_time < start:
                available_blocks.append((last_end_time, start))
            last_end_time = max(last_end_time, end)

        end_of_day = convert_to_datetime("11:50 PM")
        if last_end_time < end_of_day:
            available_blocks.append((last_end_time, end_of_day))

        for start, end in available_blocks:
            all_available_blocks.append((date, start, end))

    # Step 2: Sort blocks by date to roughly balance across days
    all_available_blocks.sort(key=lambda x: x[0])  # This naturally spreads by date

    # Step 3: Assign job search time round-robin style across days
    new_entries_by_date = {date: [] for date in schedule}
    
    # Group blocks by date
    blocks_by_date = defaultdict(deque)
    for date, start, end in all_available_blocks:
        blocks_by_date[date].append((start, end))

    date_queue = deque(sorted(blocks_by_date.keys()))  # round-robin through dates

    while remaining_job_search_time > 0 and date_queue:
        date = date_queue.popleft()
        blocks = blocks_by_date[date]

        while blocks and remaining_job_search_time > 0:
            start, end = blocks[0]
            if (end - start).seconds // 60 >= job_search_block:
                new_end = start + timedelta(minutes=job_search_block)

                # Merge with previous if possible
                entries = new_entries_by_date[date]
                if entries and entries[-1]["type"] == "JOB_SEARCH" and entries[-1]["end_time"] == format_time(start):
                    entries[-1]["end_time"] = format_time(new_end)
                else:
                    entries.append({
                        "type": "JOB_SEARCH",
                        "start_time": format_time(start),
                        "end_time": format_time(new_end)
                    })

                # Update block in queue
                blocks[0] = (new_end, end)
                remaining_job_search_time -= job_search_block
                break  # move to next date after one block assigned
            else:
                blocks.popleft()  # discard unusable block

        if blocks:  # still has time blocks left
            date_queue.append(date)

    # Step 4: Append to schedule and sort
    for date in new_entries_by_date:
        schedule[date].extend(new_entries_by_date[date])
        schedule[date].sort(key=lambda x: convert_to_datetime(x["start_time"]))
    
    # Second pass: Reclaim sleep time if necessary
    '''
    If not all the required job search time has been allocated, start reducing sleep time and reassigning it
    Start from the current day
    Each SLEEP shift can be reduced to a mimimum of 6.5 hours
    Try to balance it out between days as much as possible.
    If after reducing sleep as much as possible, and there is still job search time to assign, that's okay, it was the best we could do.
    '''
    #print("Remaining job search time: ",remaining_job_search_time)
    if remaining_job_search_time > 0:
        print("Reassigning sleep time, still need more job search time")

        # Collect all sleep blocks with metadata
        sleep_blocks = []
        for date in sorted(schedule.keys()):
            if date < today:
                continue
            for i, event in enumerate(schedule[date]):
                if event["type"] == "SLEEP":
                    start = convert_to_datetime(event["start_time"])
                    end = convert_to_datetime(event["end_time"])
                    duration = (end - start).seconds // 60
                    if duration > min_sleep:  # Can only reduce if it's above 6.5 hours
                        sleep_blocks.append({
                            "date": date,
                            "index": i,
                            "start": start,
                            "end": end,
                            "duration": duration
                        })

        # Sort sleep blocks: longest first, then earlier dates
        sleep_blocks.sort(key=lambda x: (-x["duration"], x["date"]))

        # Begin reducing in 30 min chunks
        while remaining_job_search_time > 0:
            made_change = False
            for block in sleep_blocks:
                if remaining_job_search_time <= 0:
                    break
                if block["duration"] - job_search_block < min_sleep:
                    continue  # Skip if this reduction would go below 6.5h
                
                # Trim sleep by 30 min
                block["end"] -= timedelta(minutes=job_search_block)
                block["duration"] -= job_search_block
                event = schedule[block["date"]][block["index"]]
                event["end_time"] = format_time(block["end"])

                # Insert job search immediately after
                job_search_start = block["end"]
                job_search_end = job_search_start + timedelta(minutes=job_search_block)
                job_search_event = {
                    "type": "JOB_SEARCH",
                    "start_time": format_time(job_search_start),
                    "end_time": format_time(job_search_end)
                }
                schedule[block["date"]].append(job_search_event)

                # Update state
                remaining_job_search_time -= job_search_block
                made_change = True

            if not made_change:
                break  # No more sleep can be trimmed

        # Final re-sorting of each day’s events
        for date in schedule:
            schedule[date].sort(key=lambda x: convert_to_datetime(x["start_time"]))
    else:
        #print("Enough job search time assigned, no need to reduce sleep")
        pass
    
    return schedule

def optimize_free(schedule):#Optimize free time (Do I even need this?)
    return schedule

def display_hours(schedule):#Displays the total job search hours
    total_job_search_time=0#Total job search time for the week (in hours)

    today = datetime.today().strftime("%m/%d/%Y")#Get current day
    today_dt = datetime.strptime(today, "%m/%d/%Y")
    
    # Find the start of the week (Sunday)
    week_start = today_dt - timedelta(days=today_dt.weekday() + 1)  # Sunday of the current week

    # Iterate from Sunday to Saturday
    for i in range(7):
        date_dt = week_start + timedelta(days=i)
        date_str = date_dt.strftime("%m/%d/%Y")

        if date_str in schedule:
            daily_job_search_time = 0  # Job search time for the day
            for event in schedule[date_str]:
                if event["type"] == "JOB_SEARCH":
                    start_time = convert_to_datetime(event["start_time"])
                    end_time = convert_to_datetime(event["end_time"])
                    duration = (end_time - start_time).seconds // 60  # Duration in minutes
                    daily_job_search_time += duration
                    total_job_search_time += duration

            day_name = date_dt.strftime("%A")  # e.g., "Monday"
            print(f"{day_name} ({date_str}): {daily_job_search_time / 60:.2f} hr")
    
    print(f"Total weekly job search time (hr): {total_job_search_time / 60:.2f}")#Print total job search time for the week
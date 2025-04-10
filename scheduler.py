'''
Scheduler.py
Used to optimize schedule to balance work (Amazon warehouse), sleep, and job searching
Creator: Dylan Church
Created 1/28/2025
Works success!
'''

#Import
import sys
import vto
import vet
from scheduling import load_schedule, save_schedule, display_schedule, clean_schedule, optimize_schedule, display_hours

# Main loop
schedule = load_schedule()#Schedule is dictionary where each key is a date (string)

while True:
    # Input
    print("\nWelcome to scheduler, input a number to choose an action")
    print("1. Display weekly schedule")
    print("2. Input VTO")
    print("3. Input VET")
    print("4. Display total job search hours")
    print("5. Exit")
    choice = input("Enter your choice: ")

    # Processing
    if choice == "1":
        display_schedule(schedule)  # Call the new display function
    elif choice == "2":
        schedule=clean_schedule(schedule)#Remove all non-work shifts
        schedule=vto.input_vto(schedule)# Input VTO 
        schedule=optimize_schedule(schedule)#Optimize schedule
    elif choice == "3":
        schedule=clean_schedule(schedule)#Remove all non-work shifts
        schedule=vet.input_vet(schedule)# Input VET
        schedule=optimize_schedule(schedule)#Optimize schedule
    elif choice == "4":
        display_hours(schedule)  # Display total job search hours
    elif choice == "5":
        save_schedule(schedule)  # Save before exiting
        print("Exiting scheduler...")
        break
    else:
        print("Invalid choice. Please try again.")
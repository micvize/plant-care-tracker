# plant-care-tracker / main.py

import json
import os
from datetime import datetime, timedelta, date


PLANTS_FILE = "plants.json"

def load_plants():
    bak_file = PLANTS_FILE + ".bak"

    try:
        with open(PLANTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Warning: plants.json is unreadable. Trying backup...")

        try:
            with open(bak_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("Loaded from backup. Repairing plants.json...")
            save_plants(data, skip_backup=True)  # <- heal main without clobbering good .bak
            return data
        except Exception:
            print("Backup is also unreadable. Starting fresh.")
            return []


def save_plants(plants, *, skip_backup=False):
    tmp_file = PLANTS_FILE + ".tmp"
    bak_file = PLANTS_FILE + ".bak"

    # 1) Write to a temp file
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(plants, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
        """
        DELETE:
        f.flush() → method on the file object (f is a Python file handle).
        It pushes Python’s buffered data down to the OS. os.fsync(f.fileno()) → function in the os module (standard library) that calls the operating system’s fsync.
        f.fileno() gives the OS-level file descriptor number that fsync needs. This forces the OS to write its buffers to disk.
        """
    # 2) Backup current file (unless we're healing a corrupted main)
    if not skip_backup and os.path.exists(PLANTS_FILE): #only runs if plants.json already exists (not on the very first save)
        try:
            with open(PLANTS_FILE, "rb") as source, open(bak_file, "wb") as destination: #rb read binary, wb write binary
                destination.write(source.read())
        except Exception as e:
            print(f"Warning: couldn't create backup: {e}")

    # 3) Atomically replace
    os.replace(tmp_file, PLANTS_FILE)


def show_menu():
    print("\nPlant Care Tracker")
    print("1. Add plant")
    print("2. Show plants")
    print("3. Remove plant")
    print("4. Mark plant as watered")
    print("5. Mark plant as fertilized")
    print("6. Show history")
    print("7. Show reminders")
    print("8. Exit")

        
def add_plant(plants):
    while True:
        name = input("Enter the plant name: ").strip()
        if not name:
            print("Name cannot be empty.")
            continue
        if any(p["name"].lower() == name.lower() for p in plants):
            print("A plant with that name already exists. Please choose a different name.")
            continue
        break
    
    # Ask for watering interval (days)
    while True:
        try:
            watering_interval = int(input("Watering interval (days): "))
            if watering_interval < 1:
                print("Please enter a valid number of days.")
            else:
                break
        except ValueError:
            print("Please enter a valid number.")

    # Optional: Ask for watering hour
    while True:
        hour_input = input("Optional: Hour to water (0-23, leave blank if none): ").strip()
        if not hour_input:
            watering_hour = None
            break
        try:
            watering_hour = int(hour_input)
            if 0 <= watering_hour <= 23:
                break
            else:
                print("Hour must be between 0 and 23.")
        except ValueError:
            print("Please enter a number between 0 and 23 or leave blank.")
    
    # Ask for fertilizing interval (days or months, optional)
    while True:
        unit = input("Fertilizing interval unit (d for days, m for months, leave blank for none): ").strip().lower()
        if not unit:
            fertilizing_interval = None
            break
        if unit not in ("d", "m"):
            print("Please enter 'd' for days, 'm' for months, or leave blank for none.")
            continue

        try:
            fertilizing_value = int(input(f"Fertilizing interval ({'days' if unit=='d' else 'months'}): "))
            if fertilizing_value < 1:
                print("Please enter a positive number.")
                continue

            fertilizing_interval = fertilizing_value if unit == "d" else fertilizing_value * 30
            break
        except ValueError:
            print("Please enter a valid number.")

    
    # Create plant dictionary
    plant = {
        "name": name,
        "watering_interval": watering_interval,
        "watering_hour": watering_hour,
        "fertilizing_interval": fertilizing_interval,
        "last_watered": None,
        "last_fertilized": None,
        "history": []
    }
    
    plants.append(plant)
    save_plants(plants)
    print(f"{name} added!")

# Show list of plants or searches for plant
def show_plants(plants):
    if not plants:
        print("No plants added yet.")
        return
    
    print("\nShow plants:")
    print("1. Show all plants")
    print("2. Search plant by name")

    choice = input("Choose an option (1-2): ").strip()

    if choice == "2":
        query = input("Enter plant name: ").strip().lower()
        if not query:
            print("Please enter plant name.")
            return
        matches = [p for p in plants if query in p["name"].lower()]
        if not matches:
            print(f"'{query}' not found.")
            return
        
        # If more than one match, let user pick one
        if len(matches) > 1:
            print(f"\nFound {len(matches)} plant(s):")
            for i, plant in enumerate(matches, start=1):
                print(f"{i}. {plant['name']}")
            while True:
                try:
                    sel = int(input("Select a plant number: "))
                    if 1 <= sel <= len(matches):
                        plant = matches[sel - 1]
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            print("\nFound a match")
            plant = matches[0]

        # basic info
        name = plant["name"]
        water = plant["watering_interval"]
        hour = plant.get("watering_hour")
        water_time = f" at {hour}:00" if hour is not None else ""
        fert_days = plant["fertilizing_interval"]

        if plant["fertilizing_interval"] is not None:
            fertilize_str = format_fertilize_interval(fert_days)

        last_watered = plant["last_watered"] or "Never"
        if plant["fertilizing_interval"] is not None:
            last_fertilized = plant["last_fertilized"] or "Never"

        print(f"\n{name}:")
        print(f"   Water every {water:>2} days{water_time} (Last watered: {last_watered})")
        if plant["fertilizing_interval"] is not None:
            print(f"   Fertilize every {fertilize_str} (Last fertilized: {last_fertilized})")

        # --- Actions menu ---
        print(f"\nWhat would you like to do with {plant['name']}?")
        print("3. Remove plant")
        print("4. Mark plant as watered")
        print("5. Mark plant as fertilized")
        print("6. Show history")
        print("7. Show reminders")
        print("8. Edit plant details")

        action = input("Choose an option (3-8): ").strip()
        if action == "3":
            remove_plant(plants, plant)
            return
        elif action == "4":
            mark_watered(plants, plant)
            return
        elif action == "5":
            mark_fertilized(plants, plant)
            return
        elif action == "6":
            show_history([plant])  # pass only this plant
            return
        elif action == "7":
            show_reminders([plant])  # pass only this plant
            return
        elif action == "8":
            edit_plant(plants, plant)
        else:
            print("Invalid option.")
        return

    # If user picked "Show all plants"
    for i, plant in enumerate(plants, start=1):
        name = plant["name"]
        water = plant["watering_interval"]
        hour = plant.get("watering_hour")
        water_time = f" at {hour}:00" if hour is not None else ""
        fert_days = plant["fertilizing_interval"]

        if plant["fertilizing_interval"] is not None:
            fertilize_str = format_fertilize_interval(fert_days)

        last_watered = plant["last_watered"] or "Never"
        last_fertilized = plant["last_fertilized"] or "Never"

        print(f"{i}. {name}")
        print(f"   Water every {water:>2} days{water_time} (Last watered: {last_watered})")
        if plant["fertilizing_interval"] is not None:
            print(f"   Fertilize every {fertilize_str} (Last fertilized: {last_fertilized})")

def remove_plant(plants, plant=None):
    # Remove known plant
    if plant is not None:
        confirm = input(f"Type 'yes' to confirm removing {plant['name']}: ").strip().lower()
        if confirm == "yes":
            try:
                plants.remove(plant)
                save_plants(plants)
                print(f"{plant['name']} removed!")
            except ValueError:
                print("Plant not found.")
        else:
            print("Cancelled.")
        return

    # Choose which plant to remove
    selection = pick_plant(plants, prompt="Enter number or name of the plant to remove.")
    if selection is None:
        return
    while True:
        confirm = input(f"Are you sure you want to remove {selection['name']} (y/n)? ").strip().lower()
        if confirm == "y":
            # pop by identity
            idx = next((i for i, p in enumerate(plants) if p is selection), None)
            if idx is None:
                print("Plant not found.")
                return
            removed = plants.pop(idx)
            save_plants(plants)
            print(f"{removed['name']} removed!")
        elif confirm == "n":
            print("Cancelled.")
            return
        else:
            print("Please type 'y' or 'n'")
        

# --- Mark plant as watered ---
def mark_watered(plants, plant=None):
    if not plants:
        print("No plants added yet.")
        return

    # If a specific plant is provided, skip selection
    if plant is None:
        selection = pick_plant(plants, prompt="Enter number or name of the plant watered")
        if selection is None:
            return
        plant = selection

    # Default to now (date + time)
    plant["last_watered"] = datetime.now().isoformat(timespec="minutes")
    current_dt = datetime.fromisoformat(plant["last_watered"])
    print(f"Marked as watered at {current_dt.strftime('%Y-%m-%d %H:%M')}")

    # --- Allow manual override ---
    edit = input("Would you like to enter a different date/time? (y/n): ").strip().lower()
    if edit == "y":
        while True:
            user_date = input("Enter date (YYYY-MM-DD): ").strip()
            user_time = input("Enter time (optional) (HH:MM): ").strip() or "00:00"
            try:
                dt = datetime.strptime(user_date + " " + user_time, "%Y-%m-%d %H:%M")
                plant["last_watered"] = dt.isoformat(timespec="minutes")
                print(f"Updated watered time to {dt.strftime('%Y-%m-%d %H:%M')}")
                break
            except ValueError:
                print("Invalid format. Please try again (YYYY-MM-DD and HH:MM).")

    # Add to history
    if "history" not in plant:
        plant["history"] = []
    plant["history"].append({
        "action": "watered",
        "date": plant["last_watered"],
        "notes": input("Notes (optional): ").strip() or None
    })

    save_plants(plants)

# --- Mark plant as fertilized ----
def mark_fertilized(plants, plant=None):
    if not plants:
        print("No plants added yet.")
        return

    if plant is None:
        selection = pick_plant(plants, prompt="Enter number or name of the plant fertilized.")
        if selection is None:
            return
        plant = selection

    if plant["fertilizing_interval"] is None:
        print(f"{plant['name']} does not have a fertilizing schedule.")
        return

    # --- Default to today ---
    plant["last_fertilized"] = date.today().isoformat()
    current_date = date.fromisoformat(plant["last_fertilized"])
    print(f"Marked as fertilized on {current_date.strftime('%Y-%m-%d')}")

    # --- Allow manual override ---
    edit = input("Would you like to enter a different date? (y/n): ").strip().lower()
    if edit == "y":
        while True:
            user_date = input("Enter date (YYYY-MM-DD): ").strip()
            try:
                dt_date = datetime.strptime(user_date, "%Y-%m-%d").date()
                plant["last_fertilized"] = dt_date.isoformat()
                print(f"Updated fertilized date to {dt_date.strftime('%Y-%m-%d')}")
                break
            except ValueError:
                print("Invalid date format. Please try again.")

    # --- Add to history ---
    if "history" not in plant:
        plant["history"] = []
    plant["history"].append({
        "action": "fertilized",
        "date": plant["last_fertilized"],
        "notes": input("Notes (optional): ").strip() or None
    })

    save_plants(plants)

#TODO: change selection to use pick_plant
def show_history(plants):
    if not plants:
        print("No plants added yet.")
        return

    def history_for(plant, filter_choice):
        messages = []
        if not plant.get("history"):
            messages.append("No history yet.")
        else:
            for entry in plant["history"]:
                action = entry["action"]
                if filter_choice == "2" and action != "watered":
                    continue
                if filter_choice == "3" and action != "fertilized":
                    continue
                date_str = entry["date"]
                notes = f" ({entry['notes']})" if entry["notes"] else ""
                messages.append(f"   - {action} on {date_str}{notes}")

        if messages:
            print(f"\nHistory for {plant['name']}:")
            for msg in messages:
                print(msg)

    # Single plant
    if len(plants) == 1:
        print("\nWhich history do you want to see?")
        print("1. All actions")
        print("2. Only watering")
        print("3. Only fertilizing")
        while True:
            filter_choice = input("Choose history of which action (1-3): ").strip()
            if filter_choice in ("1", "2", "3"):
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        history_for(plants[0], filter_choice)
        return

    # Choose plant from list
    print("0. Show all plants' histories")
    for i, plant in enumerate(plants, start=1):
        print(f"{i}. {plant['name']}")

    while True:
        try:
            choice = int(input("Enter the number of the plant (or 0 for all): "))
            if 0 <= choice <= len(plants):
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    print("\nWhich history do you want to see?")
    print("1. All actions")
    print("2. Only watering")
    print("3. Only fertilizing")
    while True:
        filter_choice = input("Choose history of which action (1-3): ").strip()
        if filter_choice in ("1", "2", "3"):
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    if choice == 0:
        for plant in plants:
            history_for(plant, filter_choice)
    else:
        history_for(plants[choice - 1], filter_choice)

#TODO: change selection to use pick_plant
def show_reminders(plants):
    if not plants:
        print("No plants added yet.")
        return

    today = date.today()

    def reminder_for(plant, filter_choice):
        name = plant["name"]
        messages = []

        # --- Watering reminder ---
        if filter_choice in ("1", "2", "4"):
            if plant["last_watered"]:
                last_watered_str = plant["last_watered"]
                if "T" in last_watered_str:
                    last_watered = datetime.fromisoformat(last_watered_str).date()
                else:
                    last_watered = date.fromisoformat(last_watered_str)
                next_water = last_watered + timedelta(days=plant["watering_interval"])
                days_until = (next_water - today).days
            else:
                days_until = 0

            if days_until < 0:
                watering_due = f"OVERDUE by {-days_until} days!"
            elif days_until == 0:
                watering_due = "Due today!"
            else:
                watering_due = f"Due in {days_until} days"

            if filter_choice != "4" or days_until <= 0:
                messages.append(f"   Watering: {watering_due}")

        # --- Fertilizing reminder ---
        if filter_choice in ("1", "3", "4"):
            if plant.get("fertilizing_interval") is None:
                if filter_choice != "4":
                    messages.append("   Fertilizing: No fertilizing schedule")
            else:
                if plant["last_fertilized"]:
                    last_fertilized = date.fromisoformat(plant["last_fertilized"])
                    next_fert = last_fertilized + timedelta(days=plant["fertilizing_interval"])
                    fert_days_until = (next_fert - today).days
                else:
                    fert_days_until = 0

                if fert_days_until < 0:
                    fert_due = f"OVERDUE by {-fert_days_until} days!"
                elif fert_days_until == 0:
                    fert_due = "Due today!"
                else:
                    fert_due = f"Due in {fert_days_until} days"

                if filter_choice != "4" or fert_days_until <= 0:
                    messages.append(f"   Fertilizing: {fert_due}")

        if messages:
            print(f"\n{name}")
            for msg in messages:
                print(msg)

    # Single plant
    if len(plants) == 1:
        print("\nWhich reminders do you want to see?")
        print("1. Both watering and fertilizing")
        print("2. Only watering")
        print("3. Only fertilizing")
        print("4. Overdue only")
        while True:
            filter_choice = input("Choose reminders of which type (1-4): ").strip()
            if filter_choice in ("1", "2", "3", "4"):
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
        reminder_for(plants[0], filter_choice)
        return

    # Choose plant from list
    print("0. Show all reminders")
    for i, plant in enumerate(plants, start=1):
        print(f"{i}. {plant['name']}")

    while True:
        try:
            choice = int(input("Enter the number of the plant (or 0 for all): "))
            if 0 <= choice <= len(plants):
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    print("\nWhich reminders do you want to see?")
    print("1. Both watering and fertilizing")
    print("2. Only watering")
    print("3. Only fertilizing")
    print("4. Overdue only")
    while True:
        filter_choice = input("Choose reminders of which type (1-4): ").strip()
        if filter_choice in ("1", "2", "3", "4"):
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

    if choice == 0:
        for plant in plants:
            reminder_for(plant, filter_choice)
    else:
        reminder_for(plants[choice - 1], filter_choice)

def edit_plant(plants, plant):
    print(f"\nEditing '{plant['name']}'")
    while True:
        print("\nWhat do you want to edit?")
        print("1. Rename plant")
        print("2. Change watering interval")
        print("3. Change fertilizing interval (set/update/remove)")
        print("4. Back")

        choice = input("Choose (1-4): ").strip()

        if choice == "1":
            while True:
                new_name = input("New name: ").strip()
                if not new_name:
                    print("Please enter a name.")
                    continue
                # allow same name for this plant, but block duplicates with others
                if any(p is not plant and p["name"].lower() == new_name.lower() for p in plants):
                    print("That name is already used by another plant.")
                    continue
                plant["name"] = new_name
                print("Name updated.")
                break

        elif choice == "2":
            while True:
                try:
                    new_watering = int(input("Watering interval (days):").strip())
                    if new_watering >= 1:
                        plant["watering_interval"] = new_watering
                        print("Watering interval updated.")
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid number.")

        elif choice == "3":
            print("\nFertilizing options:")
            print("1. Set/update interval")
            print("2. Remove fertilizing schedule")
            print("3. Cancel")
            sub = input("Choose (1-3): ").strip()

            if sub == "1":
                while True:
                    unit = input("Unit ('d' for days, 'm' for months): ").strip().lower()
                    if unit not in ("d", "m"):
                        print("Please enter 'd' or 'm'.")
                        continue
                    try:
                        new_fert = int(input(f"Interval in {'days' if unit=='d' else 'months'}: ").strip())
                        if new_fert < 1:
                            print("Please enter a positive number.")
                            continue
                        plant["fertilizing_interval"] = new_fert if unit == "d" else new_fert * 30
                        print("Fertilizing interval updated.")
                        break
                    except ValueError:
                        print("Please enter a valid number.")

            elif sub == "2":
                plant["fertilizing_interval"] = None
                print("Fertilizing schedule removed.")

            elif sub == "3":
                continue

            else:
                print("Invalid choice.")

        elif choice == "4":
            break
        else:
            print("Invalid choice.")

    save_plants(plants)

def format_fertilize_interval(days: int) -> str:
    if days < 30:
        return f"{days} days"
    elif days % 30 == 0:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"
    else:
        months = days // 30
        rem_days = days % 30
        return f"{months} month{'s' if months > 1 else ''} {rem_days} day{'s' if rem_days > 1 else ''}"
    
def pick_plant(plants, prompt, allow_all=False):
    """
    Ask the user for a plant by number OR by (partial) name.
    Returns:
      - a plant dict, or
      - the string 'ALL' if allow_all=True and user chose 0/'all', or
      - None if plants is empty.
    """
    if not plants:
        print("No plants added yet.")
        return None
    
    print(f"\n{prompt}")
    if allow_all:
        print("\nType 0 or 'all' for all plants.")
    print("\nPlants:")
    for i, p in enumerate(plants, start=1):
        print(f"{i}. {p['name']}")
    if allow_all:
        print("0. All")

    while True:
        choice = input(f"{prompt}: ").strip()
        
        # if user chose all
        if allow_all and (choice == "0" or choice.lower() == "all"):
            return "ALL"

        # If schose plant by number
        try:
            idx = int(choice)
            if 1 <= idx <= len(plants):
                return plants[idx - 1]
            else:
                print("Invalid number. Try again.")
                continue
        except ValueError:
            pass

        # name / partial name search
        query = choice.lower()
        matches = [p for p in plants if query in p["name"].lower()]

        if not matches:
            print("No matching plant. Try again.")
            continue
        if len(matches) == 1:
            return matches[0]

        # Pick between multiple matches
        print(f"Found {len(matches)} matches:")
        for i, p in enumerate(matches, start=1):
            print(f"{i}. {p['name']}")
        while True:
            sub = input(f"Choose 1-{len(matches)} (or 0 to search again): ").strip()
            if sub == "0":
                break  # back to outer loop to enter a new name/number
            try:
                sidx = int(sub)
                if 1 <= sidx <= len(matches):
                    return matches[sidx - 1]
                print("Invalid number.")
            except ValueError:
                print("Please enter a number.")

def main():
    plants = load_plants()
    while True:
        show_menu()
        choice = input("Choose an option: ")
        if choice == "1":
            add_plant(plants)
        elif choice == "2":
            show_plants(plants)
        elif choice == "3":
            remove_plant(plants)
        elif choice == "4":
            mark_watered(plants)
        elif choice == "5":
            mark_fertilized(plants)
        elif choice == "6":
            show_history(plants)
        elif choice == "7":
            show_reminders(plants)
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
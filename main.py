# plant-care-tracker / main.py

# Create a list of plants
plants = []

def add_plant(name):
    """Add a new plant to the list."""
    plants.append(name)
    print(f"✅ Plant '{name}' added!")

def show_plants():
    """Show all plants in the list."""
    if not plants:
        print("🌱 No plants yet.")
    else:
        print("Your plants:")
        for p in plants:
            print(" -", p)

# ----------- Simple Menu -----------
while True:
    print("\n--- Plant Care Tracker ---")
    print("1. Add a plant")
    print("2. Show plants")
    print("3. Exit")
    choice = input("Choose an option: ")

    if choice == "1":
        name = input("Enter plant name: ")
        add_plant(name)
    elif choice == "2":
        show_plants()
    elif choice == "3":
        print("Goodbye! 🌿")
        break
    else:
        print("Invalid choice, try again.")
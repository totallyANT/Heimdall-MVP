from database import db
import bcrypt


# -------------------------------
# Clear Demo Collections
# -------------------------------
async def clear_database():

    collections = [
        "residents",
        "security_guards",
        "admins",
        "alerts",
        "investigation_reports",
        "incident_patterns",
        "vehicles",
        "guest_passes",
        "group_passes",
        "worker_passes",
        "delivery_notifications"
    ]

    for collection in collections:
        await db[collection].delete_many({})

    print("✓ Database cleared")


# -------------------------------
# Seed Residents
# -------------------------------
async def seed_residents():

    residents = []

    names = [
        "Rahul Sharma",
        "Priya Reddy",
        "Arjun Mehta",
        "Sneha Kapoor",
        "Rohan Gupta",
        "Aditi Verma",
        "Karan Nair",
        "Neha Singh",
        "Vikram Joshi",
        "Meera Patel",
        "Ankit Jain",
        "Pooja Das",
        "Harsh Vora",
        "Divya Rao",
        "Siddharth Kumar"
    ]

    flats = [
        "A101","A102","A103","A104","A105",
        "B201","B202","B203","B204","B205",
        "C301","C302","C303","C304","C305"
    ]

    for i in range(15):

        temp_password = "pass123"

        residents.append({

            "id": f"RES-{101+i}",

            "flat_number": flats[i],

            "password": temp_password,

            "is_initialized": False,

            "full_name": "",

            "age": None,

            "phone": "",

            "badge": f"BDG-{101+i}",

            "vehicles": [],

            "card_status": "active",

            "trust_score": 1.0
        })

    await db.residents.insert_many(residents)

    print("✓ Residents Seeded")


# -------------------------------
# Seed Guards
# -------------------------------
async def seed_guards():

    guards = []

    for i in range(3):

        guards.append({

            "id": f"GRD-{101+i}",

            "password": "guard123",

            "is_initialized": False,

            "full_name": "",

            "phone": "",

            "age": None

        })

    await db.security_guards.insert_many(guards)

    print("✓ Guards Seeded")


# -------------------------------
# Seed Admins
# -------------------------------
async def seed_admins():

    password = bcrypt.hashpw(
        "admin123".encode(),
        bcrypt.gensalt()
    ).decode()

    admins = [

        {
            "id":"ADM-101",
            "password":password,
            "full_name":"Security Admin"
        },

        {
            "id":"ADM-102",
            "password":password,
            "full_name":"Community Admin"
        }

    ]

    await db.admins.insert_many(admins)

    print("✓ Admins Seeded")
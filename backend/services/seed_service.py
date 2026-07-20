import bcrypt
from database import db

# ==========================================================
#  CLEAR ALL DEMO DATA
# ==========================================================
def clear_database():
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
        db[collection].delete_many({})

    print("✓ Database cleared successfully.")


# ==========================================================
#  SEED DEMO RESIDENTS
# ==========================================================
def seed_residents():
    residents = []
    
    flats = [
        "A101", "A102", "A103", "A104", "A105",
        "B201", "B202", "B203", "B204", "B205",
        "C301", "C302", "C303", "C304", "C305"
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
            "trust_score": 100
        })

    db.residents.insert_many(residents)
    print("✓ 15 Residents Seeded.")


# ==========================================================
#  SEED DEMO GUARDS
# ==========================================================
def seed_guards():
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

    db.security_guards.insert_many(guards)
    print("✓ 3 Guards Seeded.")


# ==========================================================
#  SEED SYSTEM ADMINS
# ==========================================================
def seed_admins():
    password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()

    admins = [
        {
            "id": "ADM-101",
            "password": password,
            "full_name": "Security Admin"
        },
        {
            "id": "ADM-102",
            "password": password,
            "full_name": "Community Admin"
        }
    ]

    db.admins.insert_many(admins)
    print("✓ 2 System Administrators Seeded.")


# ==========================================================
#  MASTER EXECUTION CALLTRIGGER
# ==========================================================
def run_full_seed():
    print("Starting database reset...")
    clear_database()
    seed_residents()
    seed_guards()
    seed_admins()
    print("Database environment initialized successfully!")

if __name__ == "__main__":
    run_full_seed()
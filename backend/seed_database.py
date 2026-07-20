from services.seed_service import run_full_seed

def main():
    print("\n========== Heimdall Database Seeder ==========\n")
    run_full_seed()
    print("\n==============================================")
    print("Database initialization complete.")
    print("==============================================\n")

if __name__ == "__main__":
    main()
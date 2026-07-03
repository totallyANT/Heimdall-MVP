import asyncio

from services.seed_service import (
    clear_database,
    seed_residents,
    seed_guards,
    seed_admins
)


async def main():

    print("\n========== Heimdall Database Seeder ==========\n")

    await clear_database()

    await seed_residents()

    await seed_guards()

    await seed_admins()

    print("\n==============================================")
    print("Database seeded successfully.")
    print("==============================================\n")


if __name__ == "__main__":
    asyncio.run(main())
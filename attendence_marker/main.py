"""
Utility entrypoint for local backend checks against MongoDB.
"""

from database import close_pool, get_enrollment_stats, init_db


def main():
    init_db()
    stats = get_enrollment_stats()
    print("Mongo backend initialized successfully.")
    print(f"Total students: {stats.get('total_students', 0)}")
    close_pool()


if __name__ == "__main__":
    main()

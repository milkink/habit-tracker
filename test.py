import psycopg2

try:
    conn = psycopg2.connect(
        dbname="habit_tracker_drdx",
        user="habit_tracker_drdx_user",
        password="hfdaRjYTOj6bROL9MrWzb3rnuI65GGjJ",
        host="dpg-csq6glbqf0us73ec7740-a",
        port="5432"
    )
    print("Database connected successfully!")
except Exception as e:
    print("Database connection error:", e)

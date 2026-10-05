import sqlite3

email = input("Enter your registered account email: ").strip().lower()

conn = sqlite3.connect("users.db")

cursor = conn.execute(
    "UPDATE users SET is_admin = 1 WHERE email = ?",
    (email,)
)

conn.commit()

if cursor.rowcount == 1:
    print("Admin access enabled successfully.")
else:
    print("No account found with this email.")

conn.close()
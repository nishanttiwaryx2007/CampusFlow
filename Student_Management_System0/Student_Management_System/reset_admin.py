
from dotenv import load_dotenv
from getpass import getpass
from werkzeug.security import generate_password_hash
from cloudant_db import CloudantStore

# Load IBM Cloudant credentials
load_dotenv()

# Connect to existing database
db = CloudantStore()

print("\n===== ADMIN PASSWORD RESET =====")

username = input("Enter administrator username: ").strip().lower()

# Find administrator account
admin = db.find_one({
    "type": "user",
    "username": username
})

if not admin or admin.get("role") != "admin":
    print("\nAdministrator account not found!")
else:
    password = getpass("Enter new password: ")
    confirm = getpass("Confirm new password: ")

    if len(password) < 8:
        print("\nPassword must contain at least 8 characters.")

    elif password != confirm:
        print("\nPasswords do not match!")

    else:
        # Generate a secure password hash
        admin["password_hash"] = generate_password_hash(password)

        # Update existing administrator record
        db.update(admin)

        print("\nPassword reset successfully!")
        print("You can now sign in with your new password.")

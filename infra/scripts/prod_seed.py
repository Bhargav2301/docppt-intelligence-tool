import os
import sys
import argparse

# Add services/nlp to path so we can import from database/models/auth_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/nlp")))

try:
    from database import SessionLocal, engine
    import models
    from auth_utils import hash_password
    # Ensure tables are created
    models.Base.metadata.create_all(bind=engine)
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Seed production database with a developer/user account.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", required=True, help="User password (minimum 8 characters)")
    parser.add_argument("--role", default="developer", choices=["user", "developer"], help="Role of the user")

    args = parser.parse_args()

    # Enforce production constraint
    if args.email == "local_user@example.com":
        print("Error: The local development email 'local_user@example.com' is not permitted in production.")
        sys.exit(1)

    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(models.User).filter(models.User.email == args.email).first()
        if existing_user:
            print(f"Error: User with email {args.email} already exists.")
            sys.exit(1)

        # Create user
        new_user = models.User(
            email=args.email,
            full_name=args.email.split("@")[0].capitalize(),
            auth_provider="email",
            role=args.role,
            hashed_password=hash_password(args.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create user settings
        settings = models.UserSettings(user_id=new_user.id)
        db.add(settings)
        db.commit()

        print(f"Success: Successfully seeded user {args.email} with role={args.role}.")
    except Exception as e:
        print(f"Error: Failed to seed production user: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

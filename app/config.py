import os
from dotenv import load_dotenv
from typing import List, Tuple, Optional

load_dotenv()

# Load Stripe secret keys from environment variables
STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_KEY: Optional[str] = os.getenv("STRIPE_WEBHOOK_KEY")

# Discounts based on the number of team members
DISCOUNTS: List[Tuple[int, float]] = [
    (100, 0.35),  # 100+ members → 35% OFF
    (50, 0.30),   # 50+ members → 30% OFF
    (15, 0.25),   # 15+ members → 25% OFF
    (5, 0.20),    # 5+ members → 20% OFF
]

# Path to Firebase credentials
FIREBASE_CREDENTIALS_PATH: str = os.path.join(os.getcwd(), "firebase-admin-sdk.json")

# Error handling for missing environment variables
if STRIPE_SECRET_KEY is None:
    raise ValueError("Missing environment variable: STRIPE_SECRET_KEY")
if STRIPE_WEBHOOK_KEY is None:
    raise ValueError("Missing environment variable: STRIPE_WEBHOOK_KEY")

# Team Platform API

A FastAPI-based backend service for managing team members and credits, with integrated payment processing via Stripe.

## Features

- Team member management (invite, track status)
- Credit system with dynamic pricing
- Stripe integration for payments
- Firebase authentication
- Email notifications via SendGrid
- Configurable environment settings

## Prerequisites

- Python 3.12.9
- Firebase Admin SDK credentials
- Stripe API keys
- SendGrid API key
- AWS Secret and acess key
- firebase-admin-sdk-json 

## Environment Variables

Create a `.env` file with the following variables mentioned in the `.env.sample` file

## Installation

### Manual Setup

1. Create a virtual environment:

        python -m venv venv
    To activate the virtual environment, run the following command:

        source venv/bin/activate # Linux/Mac
        venv\Scripts\activate # Windows

2. Install dependencies:

        pip install -r requirements.txt

3. Run the application:


        uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## Setting Up Postman Environments


### Open Postman

1. Launch Postman and create a use Team Platform collection for your API.

### Create an Environment

1. Click on the gear icon in the left navigation bar select **Environments**.
2. Click **Add or "+" icon** to create a new environment.
3. Name the environment (e.g., Development, Testing, or Production).

### Add Environment Variables

1. Add a key-value pair for the `baseurl`:
   - **Key**: `baseurl`
   - **Value**: The base URL of your API (e.g., `http://localhost:8000` for development or your production URL).
3. Save the environment.

### Use the Environment

1. Select the environment from the dropdown in the top-right corner of Postman.
2. In your API requests, use the `{{baseurl}}` variable to dynamically switch between environments. For example:- **URL**: `{{baseurl}}/team/invite_team_member` which is already set

This will automatically replace `{{baseurl}}` with the value defined in your selected environment.

## Project Structure
    ├── app/
    │ ├── dependencies/ # Authentication and other dependencies
    │ ├── middleware/ # CORS and other middleware
    │ ├── routes/ # API route handlers
    │ ├── schema/ # Pydantic models
    │ ├── services/ # Business logic
    │ └── config.py # Application configuration
    ├── main.py # Application entry point
    ├── requirements.txt
    └── settings.py # Environment settings


## API Endpoints

### Auth

- `POST /auth/login` - Login to Firebase Manager

### Team Management

- `POST /team/invite_team_member` - Invite a new team member
- `GET /team/get_team_members` - Get list of team members
- `POST /team/send_notification` - Send notification to team member

### Credit Management

- `POST /credits/buy_credits` - Purchase credits via Stripe
- `GET /credits/get_credits` - Get available credits
- `POST /credits/invalidate_credit` - Invalidate a team member's credit
- `POST /credits/webhook` - Stripe webhook endpoint



## Team Member States

- `Pending` - Invitation sent, awaiting acceptance
- `Completed` - Team member has completed the onboarding process

## Credit System

The system includes a dynamic pricing model with team-size-based discounts:

- 100+ members: 35% OFF
- 50+ members: 30% OFF
- 15+ members: 25% OFF
- 5+ members: 20% OFF

## Error Handling

The API implements comprehensive error handling with appropriate HTTP status codes and detailed error messages.

## Development

The application supports multiple environments:
- Development
- Testing
- Production

Set the `APP_ENV` environment variable to switch between environments.

### Firebase Authentication Flow

1. Users authenticate through the `/auth/login` endpoint
2. The returned Firebase ID token must be included in subsequent API requests
3. Tokens are automatically validated using Firebase Admin SDK
4. Invalid or expired tokens will receive a 401 Unauthorized response

### Security Notes

- Firebase ID tokens expire after 1 hour
- Use refresh tokens to obtain new ID tokens
- Store tokens securely on the client side
- Never expose Firebase Admin SDK credentials

## Buy Credits & Payment Flow

The Buy Credits API workflow:
API returns a `checkout_url` that redirects users to the Stripe payment page once payment is completed manager can see the see purchased credits using `/credits/get_credits` endpoint
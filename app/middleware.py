from fastapi.middleware.cors import CORSMiddleware

def add_middleware(app):
    """Add CORS middleware to FastAPI app"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change this for security in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

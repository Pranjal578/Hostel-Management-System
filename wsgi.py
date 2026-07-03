from dotenv import load_dotenv
load_dotenv()

from app import create_app

# Instantiate the Flask application using the factory pattern
app = create_app()

# Vercel or Gunicorn processes will use this reference
application = app

if __name__ == "__main__":
    app.run()
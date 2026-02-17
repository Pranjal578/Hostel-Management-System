from dotenv import load_dotenv
load_dotenv()

from app import app

# Vercel needs this
application = app

if __name__ == "__main__":
    app.run()
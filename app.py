from dotenv import load_dotenv
load_dotenv()

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.config.get('DEBUG', True),
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000))
    )

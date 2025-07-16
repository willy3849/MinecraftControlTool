import os
import dotenv

dotenv.load_dotenv()

WEB_PORT = int(os.getenv("WEB_PORT", 3000))
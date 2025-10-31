from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":
    config = Config()
    print(config.OPENAI_API_KEY)
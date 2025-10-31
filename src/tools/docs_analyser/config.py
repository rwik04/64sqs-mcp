from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_CLIENT_ID = os.getenv("AWS_CLIENT_ID")
    AWS_PROJECT_ID = os.getenv("AWS_PROJECT_ID")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")

if __name__ == "__main__":
    print(Config.AWS_ACCESS_KEY)
    print(Config.AWS_SECRET_ACCESS_KEY)
    print(Config.AWS_BUCKET_NAME)
    print(Config.AWS_REGION)
    print(Config.AWS_CLIENT_ID)
    print(Config.AWS_PROJECT_ID)
    print(Config.LLM_API_KEY)
    print(Config.EMBEDDING_API_KEY)
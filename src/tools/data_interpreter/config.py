from dotenv import load_dotenv
import os 

load_dotenv()

class Config:
    VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    DB_URI = os.getenv("DB_URI")
    DB_NAME = os.getenv("DB_NAME")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAPI_AI_MODEL = os.getenv("OPENAPI_AI_MODEL")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_DOMAIN = os.getenv("AWS_DOMAIN")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    SOURCE_EMAIL = os.getenv("SOURCE_EMAIL")
    SOURCE_EMAIL_PASSWORD = os.getenv("SOURCE_EMAIL_PASSWORD")
    WEBSITE_URL = os.getenv("WEBSITE_URL")
    CRYPTO_KEY = os.getenv("CRYPTO_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ANNOTATION_LIMIT = os.getenv("ANNOTATION_LIMIT")

if __name__ == "__main__":
    print(Config.OPENAI_API_KEY)
    print(Config.OPENAPI_AI_MODEL)
    print(Config.AWS_BUCKET_NAME)
    print(Config.AWS_DOMAIN)
    print(Config.AWS_ACCESS_KEY)
    print(Config.AWS_SECRET_ACCESS_KEY)
    print(Config.SOURCE_EMAIL)
    print(Config.SOURCE_EMAIL_PASSWORD)
    print(Config.WEBSITE_URL)
    print(Config.CRYPTO_KEY)
    print(Config.GOOGLE_API_KEY)
    print(Config.ANNOTATION_LIMIT)
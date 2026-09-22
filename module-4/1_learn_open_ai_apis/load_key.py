from dotenv import load_dotenv
import os

print("Current directory:", os.getcwd())

result = load_dotenv()

print("Was .env loaded:", result)

api_key = os.getenv("OPENAI_API_KEY")

print("API key:", api_key)
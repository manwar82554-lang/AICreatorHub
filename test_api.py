import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("API KEY NOT FOUND")
    exit()

client = OpenAI(api_key=api_key)

try:
    response = client.responses.create(
        model="gpt-5.6",
        input="Say only: API TEST OK"
    )

    print(response.output_text)

except Exception as e:
    print("API ERROR:")
    print(e)
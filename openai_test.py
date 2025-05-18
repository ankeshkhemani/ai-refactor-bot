import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def test_openai_prompt():
    prompt = """Refactor the following Python code to improve readability and reduce complexity:\n
def add(x,y): return x+y"""

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    print(response.choices[0].message.content.strip())


if __name__ == "__main__":
    test_openai_prompt()

from google import genai

client = genai.Client(api_key="key")

response = client.models.generate_content(
    model="gemini-3.5-flash-lite", contents="Hello"
)

print(response.text)

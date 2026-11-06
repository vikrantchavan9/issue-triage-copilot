import os, requests
from dotenv import load_dotenv
load_dotenv()

# 1. Are the variables present? (prints OK/MISSING, never the values)
for k in ['GOOGLE_API_KEY', 'GITHUB_TOKEN', 'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_HOST']:
    print(k, 'OK' if os.getenv(k) else 'MISSING')

# 2. GitHub: limit should read 5000 with a token, 60 without
r = requests.get('https://api.github.com/rate_limit',
                 headers={'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'})
print('GitHub status:', r.status_code, '| hourly limit:', r.json()['resources']['core']['limit'])

# 3. Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model='gemini-3.5-flash', temperature=0)
print('Gemini says:', llm.invoke('Reply with the word ready').content)

# 4. Langfuse
from langfuse import get_client
print('Langfuse auth:', get_client().auth_check())
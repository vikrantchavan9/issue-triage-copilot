import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langfuse.langchain import CallbackHandler
from langfuse import get_client

PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')
MODEL = os.getenv('LLM_MODEL', 'qwen2.5:14b')
PROMPT_VERSION = 'triage_v1'

class Triage(BaseModel):
    category: Literal['bug', 'feature', 'question']
    severity: Literal['low', 'medium', 'high']
    summary: str = Field(description='One sentence summary of the issue')

def make_llm():
    if PROVIDER == 'ollama':
        from langchain_ollama import ChatOllama
        # num_ctx matters: Ollama's default context window is small and silently cuts long issues
        return ChatOllama(model=MODEL, temperature=0, num_ctx=8192)
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=MODEL, temperature=0)

llm = make_llm()
if PROVIDER == 'ollama':
    structured = llm.with_structured_output(Triage, method='json_schema')
else:
    structured = llm.with_structured_output(Triage)

SYSTEM = open(f'prompts/{PROMPT_VERSION}.md', encoding='utf-8').read()
prompt = ChatPromptTemplate.from_messages([
    ('system', SYSTEM),
    ('human', 'Title: {title}\n\nBody: {body}'),
])
chain = prompt | structured

def triage_issue(title, body, issue_number=None, callbacks=None):
    handler = CallbackHandler()
    return chain.invoke(
        {'title': title, 'body': body},
        config={
            'callbacks': [handler] + (callbacks or []),
            'run_name': 'triage_issue',
            'metadata': {
                'langfuse_tags': [PROMPT_VERSION, MODEL],
                'issue_number': str(issue_number),
            },
        },
    )

if __name__ == '__main__':
    import json, time
    cases = [json.loads(l) for l in open('data/golden.jsonl', encoding='utf-8')][:5]
    for c in cases:
        out = triage_issue(c['title'], c['body'], issue_number=c['number'])
        print(c['number'], '| expected:', c['expected_category'], '| got:', out.category, '|', out.severity)
        print('   ', out.summary)
        if PROVIDER != 'ollama':
            time.sleep(15)
    get_client().flush()
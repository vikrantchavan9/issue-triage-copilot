from mcp.server.fastmcp import FastMCP

mcp = FastMCP('issue-triage')

@mcp.tool()
def get_issue(number: int) -> dict:
    '''Return the title, body and labels of an issue from the local dataset.'''
    ...

@mcp.tool()
def find_similar_issues(text: str, k: int = 5) -> list[dict]:
    '''Find past issues most similar to the given text. Returns number, title and similarity.'''
    ...

@mcp.tool()
def propose_labels(number: int, labels: list[str], reply_draft: str) -> str:
    '''Save a label and reply proposal for human review. Does NOT change GitHub.'''
    ...

if __name__ == '__main__':
    mcp.run()
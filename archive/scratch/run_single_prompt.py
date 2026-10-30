import sys
sys.path.append('.')
from test_nlu import prompts
from app.database import DatabaseSession
from app.agent.nlu_engine import NLUEngine

def test_prompt(index):
    session = DatabaseSession(student_id='stu-251fa04f90')
    q = prompts[index]
    print(f'PROMPT {index+1}: {q}')
    res = NLUEngine.classify_and_reason(session, q, [], {}, 'en')
    print(f'CATEGORY: {res.get("category")}')
    print(f'RESPONSE: {res.get("content")}')
    print('-'*50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        idx = int(sys.argv[1]) - 1
        test_prompt(idx)
    else:
        test_prompt(0)

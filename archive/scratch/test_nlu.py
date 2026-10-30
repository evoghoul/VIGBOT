import json
from app.agent.nlu_engine import NLUEngine
from app.database import DatabaseSession

def test():
    session = DatabaseSession(student_id='cccccccc-0000-0000-0000-000000000001')
    eng = NLUEngine()
    res = NLUEngine.classify_and_reason(
        session=session,
        query="Where can I find MHP and Zest?",
        conversation_history=[],
        context_data={}
    )
    with open('test_res.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

test()

import sys
import os

sys.path.insert(0, os.path.abspath("BACKEND"))

from app.agent.nlu_engine import NLUEngine
from app.database import DatabaseSession, DataRepository

session = DatabaseSession(
    student_id="cccccccc-0000-0000-0000-000000000001",
    user_id="eeeeeeee-0000-0000-0000-000000000001"
)

queries = [
    "hostel bus timing",
    "is the library open on sunday",
    "where is the mess and what time is dinner",
    "how do i report a lost id card",
    "which club should i join for robotics",
    "book seminar hall tomorrow",
    "bus from guntur to college time",
    "what is my attendance in dbms and how many classes to reach 75",
    "where is u block"
]

for i, q in enumerate(queries, 1):
    res = NLUEngine.classify_and_reason(
        session=session,
        query=q,
        conversation_history=[],
        context_data={},
        language="en"
    )
    print(f"=== QUERY {i}: {q} ===")
    print(f"ROUTED_BY: {res.get('routed_by')}")
    print(f"PROVIDER: {res.get('llm_provider')}")
    print(f"MODEL: {res.get('model_used')}")
    print(f"TOPIC: {res.get('topic')}")
    print(f"CATEGORY: {res.get('category')}")
    print("CONTENT:")
    print(res.get("content", "").strip())
    print("-" * 60)


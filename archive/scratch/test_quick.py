import json
from app.database import DatabaseSession
from app.agent.nlu_engine import NLUEngine

prompts = [
    "What is my current attendance percentage in Digital Electronics?",
    "How many credits do I still need to clear this semester to meet my graduation requirements?",
    "Can you show me my mid-semester marks for Data Structures and Algorithms?"
]

def run_quick_tests():
    session = DatabaseSession(student_id="stu-251fa04f90")
    for i, p in enumerate(prompts):
        print(f"Testing: {p}")
        try:
            res = NLUEngine.classify_and_reason(session, p, [], {}, "en")
            print(f"Category: {res.get('category')}")
            print(f"Response: {res.get('content')}")
            print("-" * 40)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")

if __name__ == '__main__':
    run_quick_tests()

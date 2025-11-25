import sys
import time
from personal_assistant import DynamicPersonalAssistant

def main():
    if len(sys.argv) < 2:
        print("Usage: python assistant_cli.py \"Your question here\"")
        sys.exit(1)
    
    query = sys.argv[1]
    user_id = "default_user"
    session_id = "test_session"
    
    print(f"Question: {query}")
    print("Processing...")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        assistant = DynamicPersonalAssistant()
        result = assistant.process_query(user_id=user_id, query=query, session_id=session_id)
        elapsed_time = time.time() - start_time
        
        print()
        print(f"Answer: {result['response']}")
        
        if result['user_memories_count'] > 0:
            memories = assistant.get_user_memories(user_id)
        
        assistant.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

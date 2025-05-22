import json
import os
import sys

# Add the parent directory to sys.path to import the handler module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from handler.index import handler

def run_test():
    # Load the test event from fulfilled.json
    with open(os.path.join(os.path.dirname(__file__), 'fulfilled.json'), 'r') as f:
        event = json.load(f)
    
    # Call the handler with our test event
    result = handler(event)
    
    # Print the result
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    run_test()

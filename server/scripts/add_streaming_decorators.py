#!/usr/bin/env python3
"""
Script to automatically add streaming decorators to all agent functions.
This script will add the @with_streaming_progress decorator to all agent functions
and import the necessary utilities.
"""

import os
import re
from pathlib import Path

# Define the agent files to update
AGENT_FILES = [
    "src/agents/ben_graham.py",
    "src/agents/bill_ackman.py", 
    "src/agents/cathie_wood.py",
    "src/agents/charlie_munger.py",
    "src/agents/michael_burry.py",
    "src/agents/peter_lynch.py",
    "src/agents/phil_fisher.py",
    "src/agents/stanley_druckenmiller.py",
    "src/strategies/technical/technicals.py",
    "src/strategies/fundamentals/fundamentals.py",
    "src/strategies/valuation/valuation.py",
    "src/agents/sentiment.py",
]

def add_streaming_to_file(file_path: str):
    """Add streaming decorator and imports to a single file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add import if not present
    if "from src.utils.streaming import" not in content:
        # Find the last import line
        import_pattern = r'^from.*import.*$'
        imports = re.findall(import_pattern, content, re.MULTILINE)
        
        if imports:
            last_import = imports[-1]
            new_import = "from src.utils.streaming import with_streaming_progress, emit_ticker_progress"
            content = content.replace(last_import, f"{last_import}\n{new_import}")
        else:
            # If no imports found, add at the top after the first line
            lines = content.split('\n')
            lines.insert(1, "from src.utils.streaming import with_streaming_progress, emit_ticker_progress")
            content = '\n'.join(lines)
    
    # Find agent function definitions and add decorators
    # Pattern to match function definitions that end with "_agent"
    function_pattern = r'^def (\w+_agent)\('
    
    def add_decorator(match):
        func_name = match.group(1)
        # Extract agent name from function name
        agent_name = func_name.replace("_agent", "")
        return f"@with_streaming_progress(\"{agent_name}\")\ndef {func_name}("
    
    # Only add decorator if it's not already there
    if "@with_streaming_progress" not in content:
        content = re.sub(function_pattern, add_decorator, content, flags=re.MULTILINE)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated: {file_path}")

def main():
    """Main function to update all agent files."""
    print("Adding streaming decorators to agent functions...")
    
    for file_path in AGENT_FILES:
        add_streaming_to_file(file_path)
    
    print("Done! All agent files have been updated with streaming decorators.")
    print("\nNext steps:")
    print("1. Test the streaming functionality")
    print("2. Add emit_ticker_progress() calls within agent functions for granular progress")
    print("3. Update the workflow service to use mode='custom' for streaming")

if __name__ == "__main__":
    main() 
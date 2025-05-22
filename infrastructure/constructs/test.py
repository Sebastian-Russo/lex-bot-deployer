import json
from attr import asdict

from menu_bot.models import PromptAction

# Create a PromptAction instance
p = PromptAction(prompt='test', hang_up=False)

# Convert to dictionary first
p_dict = asdict(p)
out = json.dumps(p_dict)

print(out)

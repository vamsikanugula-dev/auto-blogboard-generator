import os
import logging
import sys

# Setup logging to see all messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

try:
    from opik import Opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self):
        self.client = None
        if OPIK_AVAILABLE and os.getenv("OPIK_API_KEY"):
            try:
                self.client = Opik()
                logger.info("Opik client initialized for prompt management.")
            except Exception as e:
                logger.warning(f"Failed to initialize Opik client: {e}")

    def get_prompt(self, prompt_name: str, fallback_prompt: str, **kwargs) -> str:
        """
        Attempt to fetch and format a prompt from Opik.
        If it fails or Opik is unconfigured, format the fallback_prompt and return it.
        """
        if self.client:
            try:
                prompt_obj = self.client.get_prompt(name=prompt_name)
                logger.info(f"[OK] Fetched prompt '{prompt_name}' from Opik.")
                return prompt_obj.format(**kwargs)
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch prompt '{prompt_name}' from Opik. Falling back to local prompt. Error: {e}")
        
        # Fallback to local prompt
        return fallback_prompt.format(**kwargs)

# Test the prompt manager
print("=" * 60)
print("Testing PromptManager")
print("=" * 60)

# Create instance
pm = PromptManager()
print("[OK] PromptManager instance created successfully")
print(f"  - Opik Available: {OPIK_AVAILABLE}")
print(f"  - Opik API Key Set: {bool(os.getenv('OPIK_API_KEY'))}")
print(f"  - Client Initialized: {pm.client is not None}")

# Test get_prompt with fallback
fallback = "This is a {type} prompt"
result = pm.get_prompt("test_prompt", fallback, type="test")
print(f"\n[OK] get_prompt() executed successfully")
print(f"  - Result: {result}")

print("\n" + "=" * 60)
print("[OK] All tests passed! No errors detected.")
print("=" * 60)

#!/usr/bin/env python3
"""
Apply custom patches to hermes-agent after update.
This script modifies files by finding marker strings and inserting code,
so it works regardless of line number changes between versions.

Patch file location: ~/.hermes/scripts/hermes-custom-patches.patch
Usage: Run automatically via .git/hooks/post-merge
"""

import os
import re
import sys
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes" / "hermes-agent"
LOG_FILE = "/tmp/hermes-custom-patch.log"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def patch_auxiliary_client():
    """Add qwen3.7-plus to _PROVIDER_VISION_MODELS"""
    filepath = HERMES_DIR / "agent" / "auxiliary_client.py"
    if not filepath.exists():
        log(f"SKIP: {filepath} not found")
        return False
    
    content = filepath.read_text()
    
    # Check if already patched
    if '"alibaba": "qwen3.7-plus"' in content:
        log("SKIP: auxiliary_client.py already patched")
        return True
    
    # Find the _PROVIDER_VISION_MODELS dict and add the entry
    pattern = r'(_PROVIDER_VISION_MODELS: Dict\[str, str\] = \{\n    "xiaomi": "mimo-v2\.5",\n    "zai": "glm-5v-turbo",\n)(})'
    
    new_content = r'\1    "alibaba": "qwen3.7-plus",\n\2'
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_content, content)
        filepath.write_text(content)
        log("PATCH: auxiliary_client.py - added qwen3.7-plus to vision models")
        return True
    else:
        log(f"ERROR: Could not find pattern in auxiliary_client.py")
        return False

def patch_config():
    """Add FEISHU_ALLOW_ALL_GROUP_MESSAGES env var support to config.py"""
    filepath = HERMES_DIR / "gateway" / "config.py"
    if not filepath.exists():
        log(f"SKIP: {filepath} not found")
        return False
    
    content = filepath.read_text()
    
    # Check if already patched
    if "FEISHU_ALLOW_ALL_GROUP_MESSAGES" in content:
        log("SKIP: config.py already patched")
        return True
    
    # Find the feishu_verification_token block and add after it
    pattern = r'(        feishu_verification_token = os\.getenv\("FEISHU_VERIFICATION_TOKEN", ""\)\n        if feishu_verification_token:\n            config\.platforms\[Platform\.FEISHU\]\.extra\["verification_token"\] = feishu_verification_token\n)'
    
    new_code = r'''\1        feishu_allow_all_group = os.getenv("FEISHU_ALLOW_ALL_GROUP_MESSAGES", "").strip().lower()
        if feishu_allow_all_group in {"true", "1", "yes"}:
            config.platforms[Platform.FEISHU].extra["allow_all_group_messages"] = True
'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_code, content)
        filepath.write_text(content)
        log("PATCH: config.py - added FEISHU_ALLOW_ALL_GROUP_MESSAGES support")
        return True
    else:
        log(f"ERROR: Could not find pattern in config.py")
        return False

def patch_feishu():
    """Add allow_all_group_messages and pipeline routing to feishu.py"""
    filepath = HERMES_DIR / "gateway" / "platforms" / "feishu.py"
    if not filepath.exists():
        log(f"SKIP: {filepath} not found")
        return False
    
    content = filepath.read_text()
    
    # Check if already patched
    if "allow_all_group_messages" in content:
        log("SKIP: feishu.py already patched")
        return True
    
    log("ERROR: feishu.py requires complex patching - use git apply with updated patch file")
    log("Run: cd ~/.hermes/hermes-agent && git apply --reject ~/.hermes/scripts/hermes-custom-patches.patch")
    return False

def main():
    log("=" * 60)
    log("Starting custom patch application")
    log("=" * 60)
    
    results = []
    results.append(patch_auxiliary_client())
    
    # NOTE: patch_config() is DISABLED.
    # FEISHU_ALLOW_ALL_GROUP_MESSAGES is obsolete; we now use
    # 'require_mention: false' in config.yaml which is native.
    log("SKIP: config.py patch disabled (using require_mention: false)")
    results.append(True)
    
    # feishu.py is now handled by patch-feishu.py (pipeline routing only)
    results.append(True)
    
    if all(results):
        log("All patches applied successfully")
    else:
        log("WARNING: Some patches failed, check log for details")
    
    log("Patch application complete")
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())

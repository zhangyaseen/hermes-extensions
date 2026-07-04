#!/usr/bin/env python3
"""
Apply custom feishu.py patches after hermes update.
This script adds pipeline routing functionality (a-stock-message-analyzer).
NOTE: require_mention is now handled via config.yaml (FEISHU_REQUIRE_MENTION=false).
"""

import sys
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes" / "hermes-agent"
FEISHU_PY = HERMES_DIR / "gateway" / "platforms" / "feishu.py"
LOG_FILE = "/tmp/hermes-custom-patch.log"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def patch_feishu():
    """Apply pipeline routing modifications to feishu.py"""
    if not FEISHU_PY.exists():
        log(f"ERROR: {FEISHU_PY} not found")
        return False
    
    content = FEISHU_PY.read_text()
    
    # Check if already patched
    if "def _should_route_to_pipeline" in content and "def _route_to_pipeline" in content:
        log("SKIP: feishu.py pipeline routing already patched")
        return True
    
    original = content
    
    # 1. Add import sys after import re
    if "import sys" not in content:
        content = content.replace(
            "import re\n",
            "import re\nimport sys\n",
            1
        )
        log("PATCH: Added 'import sys'")
    
    # 2. Add pipeline field to FeishuGroupRule
    if "pipeline: bool = False" not in content:
        content = content.replace(
            "    blacklist: set[str] = field(default_factory=set)\n\n",
            "    blacklist: set[str] = field(default_factory=set)\n    pipeline: bool = False  # If True, route message to pipeline instead of Agent\n\n",
            1
        )
        log("PATCH: Added pipeline field to FeishuGroupRule")
    
    # 3. Add pipeline parsing in _load_settings
    if "pipeline=bool(rule_cfg.get" not in content:
        content = content.replace(
            """                    blacklist=set(str(u).strip() for u in rule_cfg.get("blacklist", []) if str(u).strip()),
                )""",
            """                    blacklist=set(str(u).strip() for u in rule_cfg.get("blacklist", []) if str(u).strip()),
                    pipeline=bool(rule_cfg.get("pipeline", False)),
                )""",
            1
        )
        log("PATCH: Added pipeline parsing in _load_settings")
    
    # 4. Add pipeline routing in _dispatch_inbound_event
    if "_should_route_to_pipeline" not in content:
        content = content.replace(
            """    async def _dispatch_inbound_event(self, event: MessageEvent) -> None:
        \"\"\"Apply Feishu-specific burst protection before entering the base adapter.\"\"\"
        if event.message_type == MessageType.TEXT and not event.is_command():""",
            """    async def _dispatch_inbound_event(self, event: MessageEvent) -> None:
        \"\"\"Apply Feishu-specific burst protection before entering the base adapter.\"\"\"
        # Pipeline routing: check if message is from a pipeline-enabled group
        if self._should_route_to_pipeline(event):
            await self._route_to_pipeline(event)
            return
        if event.message_type == MessageType.TEXT and not event.is_command():""",
            1
        )
        log("PATCH: Added pipeline routing in _dispatch_inbound_event")
    
    # 5. Add _should_route_to_pipeline and _route_to_pipeline methods
    # Find the insertion point (before Media batching section or at end of class)
    markers = [
        "    # =========================================================================\n    # Media batching",
        "    # === Media batching",
        "    # Media batching",
        "    def _should_batch_media_event",
    ]
    
    if "def _should_route_to_pipeline" not in content:
        inserted = False
        for marker in markers:
            if marker in content:
                # Insert before the marker
                pipeline_methods = """    # =========================================================================
    # Pipeline routing
    # =========================================================================

    def _should_route_to_pipeline(self, event: MessageEvent) -> bool:
        \"\"\"Check if message should be routed to the a-stock pipeline instead of Agent.\"\"\"
        chat_id = event.source.chat_id
        if not chat_id:
            return False
        # Check pipeline_groups.json config
        try:
            config_path = Path(__file__).parent.parent.parent.parent / "skills" / "a-stock-message-analyzer" / "config" / "pipeline_groups.json"
            if config_path.exists():
                with open(config_path) as f:
                    cfg = json.load(f)
                pipeline_ids = cfg.get("pipeline_group_ids", [])
                if chat_id in pipeline_ids:
                    return True
        except Exception:
            pass
        # Fallback: check group_rules
        rule = self._settings.group_rules.get(chat_id)
        if rule is not None and rule.pipeline:
            return True
        return False

    async def _route_to_pipeline(self, event: MessageEvent) -> None:
        \"\"\"Route message to a-stock pipeline: enqueue + trigger pipeline runner.\"\"\"
        import subprocess
        import threading

        chat_id = event.source.chat_id
        message_id = event.message_id or ""
        sender_id = event.source.user_id or ""
        text = event.text or ""

        # Determine message type
        if event.message_type == MessageType.TEXT:
            msg_type = "text"
        elif event.message_type == MessageType.PHOTO:
            msg_type = "photo"
        elif event.message_type == MessageType.DOCUMENT:
            msg_type = "document"
        else:
            msg_type = "text"

        # Build media URLs from event
        media_urls = [u for u in (event.media_urls or [])]
        media_types = [t for t in (event.media_types or [])]

        logger.info(
            "[Feishu] Routing to pipeline: chat_id=%s message_id=%s type=%s",
            chat_id, message_id, msg_type,
        )

        # Add typing indicator
        try:
            await self.send_typing(chat_id)
        except Exception:
            pass

        def _run_pipeline():
            \"\"\"Run pipeline in a background thread to avoid blocking the gateway.\"\"\"
            try:
                # Enqueue message
                sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "skills" / "a-stock-message-analyzer"))
                from scripts.feishu_enqueue import enqueue_feishu_message
                queue_id = enqueue_feishu_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    sender_id=sender_id,
                    msg_type=msg_type,
                    content=text,
                    media_urls=media_urls,
                    media_types=media_types,
                    thread_id=event.source.thread_id,
                )
                logger.info("[Feishu] Pipeline enqueue: queue_id=%s", queue_id)

                # Run pipeline for this specific message
                skill_dir = Path(__file__).parent.parent.parent.parent / "skills" / "a-stock-message-analyzer"
                env = os.environ.copy()
                if self._settings.app_id:
                    env["FEISHU_APP_ID"] = self._settings.app_id
                if self._settings.app_secret:
                    env["FEISHU_APP_SECRET"] = self._settings.app_secret
                result = subprocess.run(
                    ["/opt/homebrew/bin/python3", "scripts/pipeline_runner.py", "--queue-id", str(queue_id)],
                    capture_output=True, text=True, cwd=str(skill_dir), timeout=300, env=env,
                )
                output = result.stdout + result.stderr
                logger.info("[Feishu] Pipeline output for queue_id=%s:\\n%s", queue_id, output[:500])
            except subprocess.TimeoutExpired:
                logger.error("[Feishu] Pipeline timeout for queue_id")
            except Exception as e:
                logger.error("[Feishu] Pipeline routing error: %s", e, exc_info=True)

        thread = threading.Thread(target=_run_pipeline, name="feishu-pipeline-router", daemon=True)
        thread.start()

"""
                content = content.replace(marker, pipeline_methods + marker, 1)
                log(f"PATCH: Added pipeline methods before '{marker[:50]}...'")
                inserted = True
                break
        
        if not inserted:
            # Fallback: append before the last line if no marker found
            log("WARNING: Could not find insertion marker, appending methods at end of file")
            # This is a last resort - should rarely happen
            return False
    
    # Write the modified content
    if content != original:
        FEISHU_PY.write_text(content)
        log("SUCCESS: feishu.py pipeline routing patched successfully")
        return True
    else:
        log("ERROR: No changes applied to feishu.py")
        return False

if __name__ == "__main__":
    success = patch_feishu()
    sys.exit(0 if success else 1)

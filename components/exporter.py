import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class TrainingDataExporter:
    def __init__(self, enabled: bool, output_path: str) -> None:
        self.enabled = enabled
        self.output_path = Path(output_path)
        if self.enabled:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def export_action(
        self,
        action: Dict[str, Any],
        decision: str,
        mirrored_tx: Optional[str],
        reason: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return

        record = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "decision": decision,
            "mirrored_tx": mirrored_tx,
            "reason": reason,
        }

        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")


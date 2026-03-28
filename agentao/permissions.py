"""Declarative permission rule engine for tool execution control."""

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PermissionDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PermissionEngine:
    """Evaluates permission rules to decide tool execution policy.

    Rules are loaded from (higher priority listed first):
    - .agentao/permissions.json  (project-level)
    - ~/.agentao/permissions.json (user-level)

    Rule format::

        {
            "rules": [
                {"tool": "run_shell_command", "args": {"command": "^git "}, "action": "allow"},
                {"tool": "write_file", "action": "ask"},
                {"tool": "run_shell_command", "args": {"command": "rm -rf"}, "action": "deny"}
            ]
        }

    When no rule matches a tool call, ``decide()`` returns ``None`` and the
    caller falls back to the tool's own ``requires_confirmation`` attribute.
    """

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self):
        """Load rules from user then project config files (project takes priority)."""
        user_rules = self._load_file(Path.home() / ".agentao" / "permissions.json")
        project_rules = self._load_file(Path.cwd() / ".agentao" / "permissions.json")
        # Project rules prepended so they are evaluated first
        self.rules = project_rules + user_rules

    def _load_file(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("rules", [])
        except (IOError, json.JSONDecodeError):
            return []

    def decide(self, tool_name: str, tool_args: Dict[str, Any]) -> Optional[PermissionDecision]:
        """Evaluate rules for a tool call.

        Returns:
            PermissionDecision.ALLOW / DENY / ASK for the first matching rule,
            or None if no rule matches (caller should use tool's requires_confirmation).
        """
        for rule in self.rules:
            if self._matches(rule, tool_name, tool_args):
                action = rule.get("action", "ask").lower()
                if action == "allow":
                    return PermissionDecision.ALLOW
                elif action == "deny":
                    return PermissionDecision.DENY
                else:
                    return PermissionDecision.ASK
        return None

    def _matches(self, rule: Dict[str, Any], tool_name: str, tool_args: Dict[str, Any]) -> bool:
        rule_tool = rule.get("tool", "*")
        if rule_tool != "*" and not self._match_pattern(rule_tool, tool_name):
            return False
        for arg_key, arg_pattern in rule.get("args", {}).items():
            arg_value = str(tool_args.get(arg_key, ""))
            try:
                if not re.search(arg_pattern, arg_value):
                    return False
            except re.error:
                if arg_pattern != arg_value:
                    return False
        return True

    def _match_pattern(self, pattern: str, value: str) -> bool:
        try:
            return bool(re.fullmatch(pattern, value))
        except re.error:
            return pattern == value

    def get_rules_display(self) -> str:
        """Return a human-readable summary of loaded rules."""
        if not self.rules:
            return (
                "No permission rules configured.\n\n"
                "Create .agentao/permissions.json to add rules.\n\n"
                "Example:\n"
                '  {"rules": [\n'
                '    {"tool": "run_shell_command", "args": {"command": "^git "}, "action": "allow"},\n'
                '    {"tool": "write_file", "action": "ask"},\n'
                '    {"tool": "*", "action": "ask"}\n'
                "  ]}"
            )

        lines = [f"Permission Rules ({len(self.rules)} total, first match wins):\n"]
        symbols = {"allow": "✓ ALLOW", "deny": "✗ DENY", "ask": "? ASK"}
        for i, rule in enumerate(self.rules, 1):
            tool = rule.get("tool", "*")
            action = rule.get("action", "ask").lower()
            args = rule.get("args", {})
            label = symbols.get(action, f"? {action.upper()}")
            line = f"  {i}. [{label}] {tool}"
            if args:
                for k, v in args.items():
                    line += f"\n        {k}: {v}"
            lines.append(line)
        return "\n".join(lines)

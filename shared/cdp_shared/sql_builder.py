"""
Translates a JSON Rule AST into a PostgreSQL WHERE clause that can be executed
against cdp.profiles (with sub-selects into cdp.events for event conditions).

Rule AST format:
{
  "operator": "AND",
  "conditions": [
    {"field": "traits.tier", "op": "eq", "value": "gold"},
    {"field": "traits.total_spend_vnd", "op": "gte", "value": 10000000},
    {
      "field": "events.booking_completed.destination",
      "op": "contains",
      "value": "Đà Nẵng",
      "time_window": {"last_n_days": 180}
    },
    {
      "operator": "OR",
      "conditions": [...]
    }
  ]
}
"""
from __future__ import annotations

from typing import Any


class SQLBuilder:
    """Convert Rule AST dict → (sql_where_clause, params_dict)."""

    def build(self, rule: dict) -> tuple[str, dict]:
        self._param_idx = 0
        self._params: dict[str, Any] = {}
        clause = self._build_node(rule)
        return clause, self._params

    def _build_node(self, node: dict) -> str:
        if "operator" in node and "conditions" in node:
            return self._build_group(node)
        return self._build_condition(node)

    def _build_group(self, node: dict) -> str:
        operator = node.get("operator", "AND").upper()
        parts = [self._build_node(c) for c in node.get("conditions", [])]
        parts = [p for p in parts if p]
        if not parts:
            return "TRUE"
        joined = f" {operator} ".join(f"({p})" for p in parts)
        return joined

    def _build_condition(self, cond: dict) -> str:
        field: str = cond["field"]
        op: str = cond["op"]
        value = cond.get("value")
        time_window = cond.get("time_window")

        if field.startswith("traits."):
            return self._trait_condition(field[7:], op, value)
        if field.startswith("events."):
            parts = field[7:].split(".", 1)
            event_type = parts[0]
            prop_path = parts[1] if len(parts) > 1 else None
            return self._event_condition(event_type, prop_path, op, value, time_window)
        if field.startswith("profile."):
            return self._profile_field_condition(field[8:], op, value)

        raise ValueError(f"Unknown field prefix in: {field}")

    # ── Trait conditions ─────────────────────────────────────────────────────

    def _trait_condition(self, trait_key: str, op: str, value) -> str:
        """cdp.profiles.traits JSONB field condition."""
        param = self._next_param(value)

        if op == "eq":
            return f"(traits->>'{trait_key}') = :{param}"
        if op == "neq":
            return f"(traits->>'{trait_key}') != :{param}"
        if op == "gt":
            return f"(traits->>'{trait_key}')::numeric > :{param}"
        if op == "gte":
            return f"(traits->>'{trait_key}')::numeric >= :{param}"
        if op == "lt":
            return f"(traits->>'{trait_key}')::numeric < :{param}"
        if op == "lte":
            return f"(traits->>'{trait_key}')::numeric <= :{param}"
        if op == "contains":
            self._params[param] = f"%{value}%"
            return f"(traits->>'{trait_key}') ILIKE :{param}"
        if op == "not_contains":
            self._params[param] = f"%{value}%"
            return f"(traits->>'{trait_key}') NOT ILIKE :{param}"
        if op == "in":
            # value should be a list
            placeholders = ", ".join(f":{self._next_param(v)}" for v in (value or []))
            return f"(traits->>'{trait_key}') IN ({placeholders})"
        if op == "not_in":
            placeholders = ", ".join(f":{self._next_param(v)}" for v in (value or []))
            return f"(traits->>'{trait_key}') NOT IN ({placeholders})"
        if op == "exists":
            return f"traits ? '{trait_key}'"
        if op == "not_exists":
            return f"NOT (traits ? '{trait_key}')"

        raise ValueError(f"Unsupported op '{op}' for trait condition")

    # ── Event conditions ─────────────────────────────────────────────────────

    # Valid event_type characters: alphanumeric + underscore only
    _EVENT_TYPE_RE = __import__("re").compile(r"^[A-Za-z0-9_]{1,100}$")

    def _event_condition(
        self, event_type: str, prop_path: str | None, op: str, value, time_window: dict | None
    ) -> str:
        """EXISTS sub-select into cdp.events."""
        # Validate event_type to prevent SQL injection — only allow safe identifiers
        if not self._EVENT_TYPE_RE.match(event_type):
            raise ValueError(f"Invalid event_type: '{event_type}' (only alphanumeric + underscore allowed)")

        et_param = self._next_param(event_type)
        subquery_parts = [
            "SELECT 1 FROM cdp.events e",
            "WHERE e.profile_id = profiles.id",
            f"AND e.event_type = :{et_param}",
        ]

        # Time window filter — parameterize dates
        if time_window:
            last_n_days = time_window.get("last_n_days")
            from_date = time_window.get("from_date")
            to_date = time_window.get("to_date")
            if last_n_days:
                # Safe: cast to int prevents injection
                subquery_parts.append(
                    f"AND e.occurred_at >= NOW() - (INTERVAL '1 day' * {int(last_n_days)})"
                )
            if from_date:
                fd_param = self._next_param(str(from_date))
                subquery_parts.append(f"AND e.occurred_at >= :{fd_param}::timestamptz")
            if to_date:
                td_param = self._next_param(str(to_date))
                subquery_parts.append(f"AND e.occurred_at <= :{td_param}::timestamptz")

        # Property filter
        if prop_path and op and value is not None:
            prop_sql = self._event_prop_condition(prop_path, op, value)
            subquery_parts.append(f"AND {prop_sql}")

        subquery = " ".join(subquery_parts)
        return f"EXISTS ({subquery})"

    def _event_prop_condition(self, prop_path: str, op: str, value) -> str:
        param = self._next_param(value)
        prop_expr = f"e.properties->>'{prop_path}'"

        if op == "eq":
            return f"{prop_expr} = :{param}"
        if op == "neq":
            return f"{prop_expr} != :{param}"
        if op == "gt":
            return f"{prop_expr}::numeric > :{param}"
        if op == "gte":
            return f"{prop_expr}::numeric >= :{param}"
        if op == "lt":
            return f"{prop_expr}::numeric < :{param}"
        if op == "lte":
            return f"{prop_expr}::numeric <= :{param}"
        if op == "contains":
            self._params[param] = f"%{value}%"
            return f"{prop_expr} ILIKE :{param}"
        if op == "not_contains":
            self._params[param] = f"%{value}%"
            return f"{prop_expr} NOT ILIKE :{param}"
        if op in ("exists", "not_exists"):
            neg = "NOT " if op == "not_exists" else ""
            return f"{neg}(e.properties ? '{prop_path}')"

        raise ValueError(f"Unsupported event prop op: {op}")

    # ── Profile field conditions ──────────────────────────────────────────────

    def _profile_field_condition(self, field: str, op: str, value) -> str:
        allowed = {"email", "phone", "loyalty_member_id", "sales_customer_id", "is_anonymous"}
        if field not in allowed:
            raise ValueError(f"Profile field '{field}' not queryable")
        param = self._next_param(value)
        if op == "eq":
            return f"{field} = :{param}"
        if op == "neq":
            return f"{field} != :{param}"
        if op == "exists":
            return f"{field} IS NOT NULL"
        if op == "not_exists":
            return f"{field} IS NULL"
        raise ValueError(f"Unsupported op '{op}' for profile field")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _next_param(self, value) -> str:
        name = f"p{self._param_idx}"
        self._param_idx += 1
        self._params[name] = value
        return name

"""验证 Agent 输出是否符合 JSON Schema。"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OutputSchemaValidator:
    """验证 Agent 输出是否符合 JSON Schema。"""

    def validate(self, agent_name: str, output: dict) -> tuple[bool, list[str]]:
        """返回 (是否通过, 错误列表)。"""
        from cloud.app.agent_runtime.core.agent_specs import AGENT_SPECS

        spec = AGENT_SPECS.get(agent_name, {})
        schema = spec.get("output_schema")
        if not schema:
            return True, []
        errors = []
        self._validate_value(output, schema, errors, "$")
        return len(errors) == 0, errors

    def coerce(self, agent_name: str, output: dict) -> dict:
        """尝试修正格式问题。修正失败返回原结果+警告。"""
        from cloud.app.agent_runtime.core.agent_specs import AGENT_SPECS

        spec = AGENT_SPECS.get(agent_name, {})
        schema = spec.get("output_schema")
        if not schema:
            return output
        result = dict(output)
        self._coerce_value(result, schema, "$")
        return result

    def _validate_value(self, value: Any, schema: dict, errors: list[str], path: str):
        schema_type = schema.get("type")
        if schema_type == "object":
            if not isinstance(value, dict):
                errors.append(f"{path}: expected object, got {type(value).__name__}")
                return
            required = schema.get("required", [])
            for field in required:
                if field not in value:
                    errors.append(f"{path}: missing required field '{field}'")
            properties = schema.get("properties", {})
            for field, field_schema in properties.items():
                if field in value:
                    self._validate_value(value[field], field_schema, errors, f"{path}.{field}")
        elif schema_type == "array":
            if not isinstance(value, list):
                errors.append(f"{path}: expected array, got {type(value).__name__}")
                return
            items_schema = schema.get("items", {})
            for i, item in enumerate(value):
                self._validate_value(item, items_schema, errors, f"{path}[{i}]")
        elif schema_type in ("string", "number", "integer", "boolean"):
            expected_type = {"string": str, "number": (int, float), "integer": int, "boolean": bool}[schema_type]
            if not isinstance(value, expected_type):
                errors.append(f"{path}: expected {schema_type}, got {type(value).__name__}")
            if schema_type == "string" and "enum" in schema:
                if value not in schema["enum"]:
                    errors.append(f"{path}: value '{value}' not in enum {schema['enum']}")
            if schema_type == "number" and isinstance(value, (int, float)):
                if "minimum" in schema and value < schema["minimum"]:
                    errors.append(f"{path}: {value} < minimum {schema['minimum']}")
                if "maximum" in schema and value > schema["maximum"]:
                    errors.append(f"{path}: {value} > maximum {schema['maximum']}")

    def _coerce_value(self, value: Any, schema: dict, path: str) -> Any:
        schema_type = schema.get("type")
        if schema_type == "object" and isinstance(value, dict):
            properties = schema.get("properties", {})
            result = {}
            for field, field_schema in properties.items():
                if field in value:
                    result[field] = self._coerce_value(value[field], field_schema, f"{path}.{field}")
            for field in value:
                if field not in properties:
                    result[field] = value[field]
                    continue
                lc_match = next((k for k in properties if k.lower() == field.lower() and k != field), None)
                if lc_match and field not in result:
                    result[lc_match] = self._coerce_value(value[field], properties[lc_match], f"{path}.{lc_match}")
            if not result:
                result = value
            return result
        if schema_type == "array" and isinstance(value, list):
            items_schema = schema.get("items", {})
            return [self._coerce_value(item, items_schema, f"{path}[{i}]") for i, item in enumerate(value)]
        return value

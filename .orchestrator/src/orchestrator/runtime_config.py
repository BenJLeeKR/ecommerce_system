"""Orchestrator 전용 런타임 환경 설정 로더."""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, Optional, Union


_ENV_KEY_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_DEFAULT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class RuntimeConfigError(ValueError):
    """런타임 설정 파일을 안전하게 읽을 수 없을 때 발생하는 예외."""


@dataclass(frozen=True)
class JulesRuntimeConfig:
    """Jules 호출에만 사용하는 비밀 런타임 설정."""

    api_key: str = field(repr=False)
    source_resource_name: str = field(repr=False)


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    """최소 .env 형식을 파싱하며, 값은 예외 메시지에 포함하지 않는다."""
    if not env_path.is_file():
        raise RuntimeConfigError(f"런타임 설정 파일을 찾을 수 없습니다: {env_path}")

    values: Dict[str, str] = {}
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise RuntimeConfigError("런타임 설정 파일을 읽을 수 없습니다.") from error

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not _ENV_KEY_PATTERN.fullmatch(key.strip()):
            raise RuntimeConfigError(f"런타임 설정 파일 {line_number}행의 형식이 올바르지 않습니다.")
        if key in values:
            raise RuntimeConfigError(f"런타임 설정 파일에 중복 키가 있습니다: {key}")

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]
        values[key] = value

    return values


def load_jules_api_key(env_file: Optional[Union[str, Path]] = None) -> str:
    """.orchestrator/.env 또는 명시 경로에서 Jules API 키만 읽는다."""
    env_path = Path(env_file) if env_file is not None else _DEFAULT_ENV_FILE
    api_key = _parse_env_file(env_path).get("JULES_API_KEY", "").strip()
    if not api_key:
        raise RuntimeConfigError("필수 런타임 설정이 비어 있습니다: JULES_API_KEY")
    return api_key


def load_jules_runtime_config(
    env_file: Optional[Union[str, Path]] = None,
) -> JulesRuntimeConfig:
    """.orchestrator/.env 또는 명시 경로에서 Jules 런타임 설정을 읽는다.

    이 함수는 값을 로그·결과 패키지·예외 메시지에 기록하지 않는다. 호출자는 반환값을
    실제 Jules API 호출 직전에만 사용해야 하며, 저장소·PR·문서에 저장해서는 안 된다.
    """
    env_path = Path(env_file) if env_file is not None else _DEFAULT_ENV_FILE
    values = _parse_env_file(env_path)

    api_key = values.get("JULES_API_KEY", "").strip()
    source_resource_name = values.get("JULES_SOURCE_RESOURCE_NAME", "").strip()

    missing_keys = []
    if not api_key:
        missing_keys.append("JULES_API_KEY")
    if not source_resource_name:
        missing_keys.append("JULES_SOURCE_RESOURCE_NAME")
    if missing_keys:
        raise RuntimeConfigError(
            "필수 런타임 설정이 비어 있습니다: " + ", ".join(missing_keys)
        )

    return JulesRuntimeConfig(
        api_key=api_key,
        source_resource_name=source_resource_name,
    )


def get_default_env_file_path() -> Path:
    """기본 .env 경로를 값 노출 없이 반환한다."""
    return _DEFAULT_ENV_FILE

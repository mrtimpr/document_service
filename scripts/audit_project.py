#!/usr/bin/env python
"""Статически проверить структуру и ключевые требования дипломного проекта."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_LINE_LENGTH = 88

# Эти файлы подтверждают наличие основных частей поставки.
REQUIRED_FILES = (
    "README.md",
    ".env.template",
    ".flake8",
    ".coveragerc",
    "Dockerfile",
    "docker-compose.yml",
    "pytest.ini",
    "pyproject.toml",
    "config/settings.py",
    "config/celery.py",
    "config/urls.py",
    "documents/models.py",
    "documents/admin.py",
    "documents/tasks.py",
    "documents/views.py",
    "documents/tests/test_api.py",
    "users/models.py",
)

# Маркеры связывают критерии задания с конкретной реализацией в коде.
REQUIRED_MARKERS = {
    "config/settings.py": (
        "django.db.backends.postgresql",
        "rest_framework",
        "drf_spectacular",
        "CELERY_BROKER_URL",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
    ),
    "documents/views.py": (
        "DocumentCreateSerializer",
        "notify_admin_about_new_document.delay",
    ),
    "documents/admin.py": (
        "approve_documents",
        "reject_documents",
    ),
    "documents/tasks.py": (
        "notify_admin_about_new_document",
        "notify_user_about_document_status",
        "send_mail",
    ),
    "docker-compose.yml": (
        "postgres:16",
        "redis:7",
        "celery",
        "nginx",
    ),
    "pytest.ini": ("--cov-fail-under=75",),
}


def iter_python_files() -> list[Path]:
    """Вернуть Python-файлы, исключив автоматически созданные миграции."""
    return [
        path
        for path in PROJECT_ROOT.rglob("*.py")
        if "migrations" not in path.parts and "__pycache__" not in path.parts
    ]


def check_required_files(errors: list[str]) -> None:
    """Проверить присутствие обязательных файлов проекта."""
    for relative_path in REQUIRED_FILES:
        if not (PROJECT_ROOT / relative_path).is_file():
            errors.append(f"Отсутствует обязательный файл: {relative_path}")


def check_markers(errors: list[str]) -> None:
    """Проверить наличие технологических маркеров в конфигурации и коде."""
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(
                    f"В файле {relative_path} отсутствует маркер: {marker}"
                )


def check_python_style(errors: list[str]) -> None:
    """Проверить синтаксис, модульные docstring и длину строк Python-кода."""
    for path in iter_python_files():
        relative_path = path.relative_to(PROJECT_ROOT)
        content = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content, filename=str(relative_path))
        except SyntaxError as exc:
            errors.append(f"Синтаксическая ошибка в {relative_path}: {exc}")
            continue

        if ast.get_docstring(tree) is None:
            errors.append(f"Нет модульного docstring: {relative_path}")

        for line_number, line in enumerate(content.splitlines(), start=1):
            if len(line) > MAX_LINE_LENGTH:
                errors.append(
                    f"Строка длиннее {MAX_LINE_LENGTH} символов: "
                    f"{relative_path}:{line_number}"
                )


def main() -> int:
    """Выполнить все проверки и вернуть код завершения для CI."""
    errors: list[str] = []
    check_required_files(errors)
    check_markers(errors)
    check_python_style(errors)

    if errors:
        print("Статический аудит завершился с ошибками:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Статический аудит пройден успешно.")
    print(f"Проверено Python-файлов: {len(iter_python_files())}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

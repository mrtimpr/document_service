#!/usr/bin/env python
"""Командная точка входа для административных команд Django."""

import os
import sys


def main() -> None:
    """Запустить команду Django, переданную через аргументы командной строки."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django не установлен или недоступен в переменной PYTHONPATH."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

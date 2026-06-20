"""Error code module."""

from enum import IntEnum


class ErrorCode(IntEnum):
    SUCCESS = 0
    UNAUTHORIZED = 1
    FORBIDDEN = 2
    NOT_FOUND = 3
    VALIDATION_ERROR = 4
    INTERNAL_ERROR = 5
    CONFLICT = 6
    RATE_LIMITED = 7

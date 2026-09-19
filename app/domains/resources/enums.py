from enum import StrEnum


class ResourceType(StrEnum):
    BOOK = "book"
    PAPER = "paper"
    COURSE = "course"
    ARTICLE = "article"
    VIDEO = "video"
    DOCUMENTATION = "documentation"
    REPOSITORY = "repository"
    WEBSITE = "website"
    FILE = "file"
    TOOL = "tool"
    OTHER = "other"


class ResourceStatus(StrEnum):
    SAVED = "saved"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
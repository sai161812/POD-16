from sqlalchemy.orm import Session

from app.domains.profile.model import (
    PersonalProfile,
)


class ProfileRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def get(
        self,
    ) -> PersonalProfile | None:
        return self.db.get(
            PersonalProfile,
            1,
        )

    def add(
        self,
        profile: PersonalProfile,
    ) -> PersonalProfile:
        self.db.add(profile)
        self.db.flush()
        self.db.refresh(profile)

        return profile
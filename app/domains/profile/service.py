from sqlalchemy.orm import Session

from app.domains.profile.model import (
    PersonalProfile,
)
from app.domains.profile.repository import (
    ProfileRepository,
)
from app.domains.profile.schemas import (
    ProfileUpdate,
)


class ProfileService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db
        self.repo = ProfileRepository(db)

    def get(
        self,
    ) -> PersonalProfile:
        profile = self.repo.get()

        if profile is None:
            profile = PersonalProfile(
                singleton_key=1,
            )

            self.repo.add(profile)

            self.db.commit()
            self.db.refresh(profile)

        return profile

    def update(
        self,
        payload: ProfileUpdate,
    ) -> PersonalProfile:
        profile = self.get()

        changes = payload.model_dump(
            exclude_unset=True
        )

        if "metadata" in changes:
            changes["extra_metadata"] = (
                changes.pop("metadata")
            )

        for field, value in changes.items():
            if value is not None:
                setattr(
                    profile,
                    field,
                    value,
                )

        self.db.commit()
        self.db.refresh(profile)

        return profile
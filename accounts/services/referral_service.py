from urllib.parse import quote
from datetime import datetime, timezone
import secrets
import string

from sqlalchemy.orm import Session

from accounts.models.referral import ReferralORM
from accounts.models.user import UserORM


REFERRAL_CODE_LENGTH = 8

TELEGRAM_BOT_USERNAME = "LookForPingBot"


def get_referral_link(
    referral_code: str,
) -> str:
    """
    Generate the user's permanent Telegram referral link.
    """

    return (
        f"https://t.me/{TELEGRAM_BOT_USERNAME}"
        f"?start=ref_{referral_code}"
    )


def get_share_link(
    referral_code: str,
) -> str:
    """
    Generate Telegram's native share URL.
    """

    referral_link = get_referral_link(
        referral_code
    )

    text = (
        "I've been using Ping to stop watching "
        "charts all day.\n\n"
        "Ping alerts you when it's time to "
        "open your charts.\n\n"
        "Try Ping:"
    )

    return (
        "https://t.me/share/url"
        f"?url={quote(referral_link)}"
        f"&text={quote(text)}"
    )


def get_referral_count(
    session: Session,
    user_id: int,
) -> int:
    """
    Return the total number of users referred
    by this user.
    """

    return (
        session.query(ReferralORM)
        .filter(
            ReferralORM.referrer_user_id == user_id
        )
        .count()
    )


def create_referral(
    session: Session,
    referrer: UserORM,
    referred_user: UserORM,
) -> ReferralORM | None:
    """
    Create a referral relationship.

    A referred user can only have one referrer.
    """

    # Don't allow self-referrals
    if referrer.id == referred_user.id:
        return None

    # Don't overwrite an existing referral
    existing = (
        session.query(ReferralORM)
        .filter(
            ReferralORM.referred_user_id
            == referred_user.id
        )
        .first()
    )

    if existing is not None:
        return existing

    referral = ReferralORM(
        referrer_user_id=referrer.id,
        referred_user_id=referred_user.id,
        referral_code=referrer.referral_code,
        created_at=datetime.now(timezone.utc),
    )

    session.add(referral)
    session.commit()
    session.refresh(referral)

    return referral

def find_user_by_referral_code(
    session: Session,
    referral_code: str,
) -> UserORM | None:
    """
    Find the user who owns a referral code.
    """

    if not referral_code:
        return None

    normalized_code = referral_code.strip().upper()

    return (
        session.query(UserORM)
        .filter(
            UserORM.referral_code == normalized_code
        )
        .first()
    )

def generate_referral_code() -> str:
    """
    Generate a short, URL-safe referral code.
    """

    alphabet = string.ascii_uppercase + string.digits

    return "".join(
        secrets.choice(alphabet)
        for _ in range(REFERRAL_CODE_LENGTH)
    )


def get_or_create_referral_code(
    session: Session,
    user: UserORM,
) -> str:
    """
    Return the user's existing referral code.

    If the user does not have one, generate a unique
    code, save it, and return it.
    """

    if user.referral_code:
        return user.referral_code

    while True:

        code = generate_referral_code()

        existing_user = (
            session.query(UserORM)
            .filter(
                UserORM.referral_code == code
            )
            .first()
        )

        if existing_user is None:
            break

    user.referral_code = code

    session.commit()

    return code
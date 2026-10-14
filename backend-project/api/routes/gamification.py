from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.models import UserGamification
from services.streak_service import StreakService
from api.routes.auth import get_current_user

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@router.get("")
def get_gamification_status(
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Ensure gamification metrics and evolution are up-to-date
    StreakService.check_avatar_evolution(db, current_user.id)

    gam = db.query(UserGamification).filter(
        UserGamification.user_id == current_user.id
    ).first()

    if not gam:
        gam = UserGamification(user_id=current_user.id)
        db.add(gam)
        db.commit()
        db.refresh(gam)

    return {
        "avatar_stage":            gam.current_stage,
        "total_active_days":       gam.total_active_days,
        "total_successful_weeks":  gam.total_successful_weeks,
        "progress_to_chick_pct":   min(100, round((gam.total_active_days / 30) * 100)),
        "progress_to_bird_pct":    min(100, round((gam.total_active_days / 60) * 100)),
        "egg_hatched_at":          gam.egg_hatched_at,
        "baby_bird_evolved_at":    gam.baby_bird_evolved_at,
        "flying_bird_evolved_at":  gam.flying_bird_evolved_at,
    }

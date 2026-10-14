from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from database import get_db
from models.models import WeeklyGoal
from api.routes.auth import get_current_user

router = APIRouter(prefix="/api/goals", tags=["goals"])


class GoalRequest(BaseModel):
    target_hours_per_week: float
    target_days_per_week:  int


@router.post("")
def set_goal(
    req:         GoalRequest,
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not 1 <= req.target_days_per_week <= 7:
        raise HTTPException(status_code=400, detail="Days per week must be between 1 and 7.")

    # Close existing active goals
    existing_goals = db.query(WeeklyGoal).filter(
        WeeklyGoal.user_id  == current_user.id,
        WeeklyGoal.ended_at.is_(None),
    ).all()

    for eg in existing_goals:
        eg.ended_at = date.today()

    goal = WeeklyGoal(
        user_id               = current_user.id,
        target_hours_per_week = req.target_hours_per_week,
        target_days_per_week  = req.target_days_per_week,
        started_at            = date.today(),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return {
        "message":              "Goal set successfully",
        "target_days_per_week": goal.target_days_per_week,
        "target_hours_per_week": float(goal.target_hours_per_week),
    }


@router.get("/active")
def get_active_goal(
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    goal = db.query(WeeklyGoal).filter(
        WeeklyGoal.user_id  == current_user.id,
        WeeklyGoal.ended_at.is_(None),
    ).first()

    if not goal:
        raise HTTPException(status_code=404, detail="No active goal found.")

    return {
        "target_days_per_week":  goal.target_days_per_week,
        "target_hours_per_week": float(goal.target_hours_per_week),
        "started_at":            goal.started_at.isoformat(),
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

from database import get_db
from models.models import (
    Workout, WorkoutExercise, WorkoutSet, Exercise,
    WeeklyCycle, WeekStatus, UserGamification
)
from services.streak_service import StreakService
from api.routes.auth import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SetInput(BaseModel):
    set_number: int
    reps:       int
    weight:     float
    rpe:        Optional[float] = None

class ExerciseInput(BaseModel):
    name:         str
    muscle_group: Optional[str] = None
    sets:         List[SetInput] = []

class LogWorkoutRequest(BaseModel):
    workout_date: date
    exercises:    List[ExerciseInput] = []

class LogSetRequest(BaseModel):
    workout_exercise_id: str
    set_number:          int
    reps:                int
    weight:              float
    rpe:                 Optional[float] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/log")
def log_workout(
    req:          LogWorkoutRequest,
    db:           Session = Depends(get_db),
    current_user  = Depends(get_current_user),
):
    """Log a workout for a given date, optionally with exercises and sets, and update the cycle."""
    try:
        result = StreakService.log_workout_and_update_cycle(
            db=db,
            user_id=str(current_user.id),
            workout_date=req.workout_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    workout = result.get("workout")

    # If exercises and sets were provided with the workout log
    if workout and req.exercises:
        for idx, ex_data in enumerate(req.exercises):
            # Find or create Exercise record
            exercise = db.query(Exercise).filter(Exercise.name == ex_data.name).first()
            if not exercise:
                exercise = Exercise(
                    name=ex_data.name,
                    muscle_group=ex_data.muscle_group,
                    is_custom=False,
                )
                db.add(exercise)
                db.flush()

            # Find or create WorkoutExercise link
            we = db.query(WorkoutExercise).filter(
                and_(
                    WorkoutExercise.workout_id == workout.id,
                    WorkoutExercise.exercise_id == exercise.id,
                )
            ).first()

            if not we:
                we = WorkoutExercise(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    order_index=idx,
                )
                db.add(we)
                db.flush()

            # Add sets
            for s in ex_data.sets:
                existing_set = db.query(WorkoutSet).filter(
                    and_(
                        WorkoutSet.workout_exercise_id == we.id,
                        WorkoutSet.set_number == s.set_number,
                    )
                ).first()

                if not existing_set:
                    new_set = WorkoutSet(
                        workout_exercise_id=we.id,
                        set_number=s.set_number,
                        reps=s.reps,
                        weight=s.weight,
                        rpe=s.rpe,
                    )
                    db.add(new_set)

        db.commit()
        StreakService._upsert_daily_metrics(db, current_user.id, req.workout_date)

    return {
        "message":           "Workout logged successfully",
        "workout_id":        str(workout.id) if workout else None,
        "status":            result["status"],
        "cycle_status":      result["cycle"].status,
        "completed_days":    result["completed_days"],
        "target_days":       result["target_days"],
        "auto_rest_enabled": result["auto_rest_enabled"],
    }


@router.get("/streak")
def get_streak(
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return current streak and gamification status."""
    current_streak = StreakService.calculate_current_streak(db, str(current_user.id))

    gam = db.query(UserGamification).filter(
        UserGamification.user_id == current_user.id
    ).first()

    if not gam:
        gam = UserGamification(user_id=current_user.id)
        db.add(gam)
        db.commit()
        db.refresh(gam)

    return {
        "current_streak_weeks":    current_streak,
        "avatar_stage":            gam.current_stage,
        "total_successful_weeks":  gam.total_successful_weeks,
        "total_active_days":       gam.total_active_days,
        "progress_to_chick":       min(100, round((gam.total_active_days / 30) * 100)),
        "progress_to_flying_bird": min(100, round((gam.total_active_days / 60) * 100)),
    }


@router.get("/weekly-cycle")
def get_weekly_cycle(
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Return the current week's cycle status."""
    today = date.today()
    week_start, week_end = StreakService.get_week_bounds(today)

    cycle = db.query(WeeklyCycle).filter(
        and_(
            WeeklyCycle.user_id         == current_user.id,
            WeeklyCycle.week_start_date == week_start,
        )
    ).first()

    if not cycle:
        return {
            "week_start":        week_start.isoformat(),
            "week_end":          week_end.isoformat(),
            "completed_days":    0,
            "target_days":       3,
            "status":            "pending",
            "auto_rest_enabled": False,
        }

    return {
        "week_start":        cycle.week_start_date.isoformat(),
        "week_end":          cycle.week_end_date.isoformat(),
        "completed_days":    cycle.completed_days,
        "target_days":       cycle.target_days,
        "status":            cycle.status,
        "auto_rest_enabled": cycle.auto_rest_enabled,
        "auto_rest_start":   cycle.auto_rest_start_date.isoformat() if cycle.auto_rest_start_date else None,
    }


@router.post("/sets")
def log_set(
    req:         LogSetRequest,
    db:          Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Log a single set for a workout exercise with ownership check."""
    exercise = db.query(WorkoutExercise).filter(
        WorkoutExercise.id == req.workout_exercise_id
    ).first()

    if not exercise:
        raise HTTPException(status_code=404, detail="Workout exercise not found.")

    workout = db.query(Workout).filter(Workout.id == exercise.workout_id).first()
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to log sets for this workout.")

    # Prevent duplicate set numbers
    existing = db.query(WorkoutSet).filter(
        and_(
            WorkoutSet.workout_exercise_id == req.workout_exercise_id,
            WorkoutSet.set_number          == req.set_number,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Set already logged.")

    workout_set = WorkoutSet(
        workout_exercise_id = req.workout_exercise_id,
        set_number          = req.set_number,
        reps                = req.reps,
        weight              = req.weight,
        rpe                 = req.rpe,
    )
    db.add(workout_set)
    db.commit()
    db.refresh(workout_set)

    # Recalculate daily metrics
    StreakService._upsert_daily_metrics(db, current_user.id, workout.workout_date)

    best_score = req.reps * req.weight

    return {
        "message":    "Set logged",
        "set_number": req.set_number,
        "reps":       req.reps,
        "weight":     req.weight,
        "best_score": best_score,
    }


@router.post("/admin/finalize-weeks")
def finalize_past_weeks(
    db:           Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Cron / admin endpoint — finalize all pending cycles whose week has passed.
    Requires authentication.
    """
    today = date.today()

    pending = db.query(WeeklyCycle).filter(
        and_(
            WeeklyCycle.week_end_date < today,
            WeeklyCycle.status        == WeekStatus.PENDING,
        )
    ).all()

    count = 0
    for cycle in pending:
        StreakService.finalize_week(db, str(cycle.user_id), cycle.week_start_date)
        count += 1

    return {"finalized_weeks": count}

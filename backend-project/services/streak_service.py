from datetime import date, datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from models.models import (
    WeeklyCycle, WeeklyGoal, Workout, WorkoutExercise, WorkoutSet,
    StreakSnapshot, UserGamification, WorkoutMetricsDaily,
    WeekStatus, AvatarStage
)


class StreakService:
    """
    Core streak + gamification logic.

    Anti-exploit guarantees:
    - Workouts cannot be logged for future dates
    - Workouts cannot be backdated beyond the current week
    - Only one workout counts per calendar day
    - Auto-rest only activates AFTER the goal is legitimately met within the week
    - Weekly cycles are locked once finalised (SUCCESS / FAILED)
    - Streak counts only consecutive SUCCESS weeks — calendar week gaps break the streak
    """

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_week_bounds(target_date: date) -> Tuple[date, date]:
        """Return Monday–Sunday bounds for a given date."""
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end   = week_start + timedelta(days=6)
        return week_start, week_end

    # ── Weekly Cycle ─────────────────────────────────────────────────────────

    @staticmethod
    def get_or_create_weekly_cycle(
        db: Session, user_id: str, target_date: date
    ) -> WeeklyCycle:
        week_start, week_end = StreakService.get_week_bounds(target_date)

        cycle = db.query(WeeklyCycle).filter(
            and_(
                WeeklyCycle.user_id == user_id,
                WeeklyCycle.week_start_date == week_start,
            )
        ).first()

        if cycle:
            return cycle

        active_goal = db.query(WeeklyGoal).filter(
            and_(
                WeeklyGoal.user_id == user_id,
                WeeklyGoal.ended_at.is_(None),
            )
        ).first()

        if not active_goal:
            raise ValueError("No active weekly goal. Please set a goal first.")

        cycle = WeeklyCycle(
            user_id          = user_id,
            week_start_date  = week_start,
            week_end_date    = week_end,
            weekly_goal_id   = active_goal.id,
            target_days      = active_goal.target_days_per_week,
            completed_days   = 0,
            status           = WeekStatus.PENDING,
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        return cycle

    # ── Log Workout ───────────────────────────────────────────────────────────

    @staticmethod
    def log_workout_and_update_cycle(
        db: Session, user_id: str, workout_date: date
    ) -> dict:
        """
        Log a workout and update the weekly cycle and gamification status.
        Returns a summary dict consumed by the API route.
        """
        today                 = date.today()
        current_week_start, _ = StreakService.get_week_bounds(today)
        workout_week_start, _ = StreakService.get_week_bounds(workout_date)

        # ── Anti-exploit: no future dates ───────────────────────────────────
        if workout_date > today:
            raise ValueError("Cannot log workouts for future dates.")

        # ── Anti-exploit: no backdating beyond current week ────────────────
        if workout_week_start < current_week_start:
            raise ValueError("Cannot log workouts for past weeks.")

        cycle = StreakService.get_or_create_weekly_cycle(db, user_id, workout_date)

        # ── One workout per day ────────────────────────────────────────────
        existing = db.query(Workout).filter(
            and_(
                Workout.user_id      == user_id,
                Workout.workout_date == workout_date,
            )
        ).first()

        if existing:
            return {
                "status":           "already_logged",
                "cycle":            cycle,
                "workout":          existing,
                "auto_rest_enabled": cycle.auto_rest_enabled,
                "completed_days":   cycle.completed_days,
                "target_days":      cycle.target_days,
            }

        # ── Create workout record ──────────────────────────────────────────
        workout = Workout(
            user_id      = user_id,
            workout_date = workout_date,
            started_at   = datetime.utcnow(),
        )
        db.add(workout)

        # ── Update cycle ───────────────────────────────────────────────────
        cycle.completed_days += 1

        if cycle.completed_days >= cycle.target_days and not cycle.auto_rest_enabled:
            cycle.auto_rest_enabled    = True
            cycle.auto_rest_start_date = workout_date + timedelta(days=1)
            cycle.status               = WeekStatus.SUCCESS

        db.commit()
        db.refresh(cycle)
        db.refresh(workout)

        # ── Update daily metrics (for ML) ─────────────────────────────────
        StreakService._upsert_daily_metrics(db, user_id, workout_date)

        # ── Real-time Gamification & Avatar Evolution Update ──────────────
        StreakService.check_avatar_evolution(db, user_id)

        return {
            "status":           "success",
            "cycle":            cycle,
            "workout":          workout,
            "auto_rest_enabled": cycle.auto_rest_enabled,
            "completed_days":   cycle.completed_days,
            "target_days":      cycle.target_days,
        }

    # ── Finalize Week (cron) ──────────────────────────────────────────────────

    @staticmethod
    def finalize_week(
        db: Session, user_id: str, week_start_date: date
    ) -> WeeklyCycle:
        """
        Lock a week as SUCCESS or FAILED.
        Called by a Monday midnight cron job for all pending cycles.
        """
        cycle = db.query(WeeklyCycle).filter(
            and_(
                WeeklyCycle.user_id         == user_id,
                WeeklyCycle.week_start_date == week_start_date,
            )
        ).first()

        if not cycle:
            raise ValueError("Weekly cycle not found.")

        # Already locked — do nothing
        if cycle.status in [WeekStatus.SUCCESS, WeekStatus.FAILED]:
            return cycle

        cycle.status = (
            WeekStatus.SUCCESS
            if cycle.completed_days >= cycle.target_days
            else WeekStatus.FAILED
        )
        db.commit()

        StreakService.update_streak_snapshot(db, user_id, cycle.week_end_date)
        StreakService.check_avatar_evolution(db, user_id)
        return cycle

    # ── Streak Calculation ────────────────────────────────────────────────────

    @staticmethod
    def calculate_current_streak(db: Session, user_id: str) -> int:
        """
        Walk backwards through weekly cycles.
        A FAILED week breaks the streak. PENDING weeks are skipped (current week in progress).
        Missing calendar weeks without SUCCESS also break the streak.
        """
        today = date.today()
        current_week_start, _ = StreakService.get_week_bounds(today)

        cycles = (
            db.query(WeeklyCycle)
            .filter(WeeklyCycle.user_id == user_id)
            .order_by(WeeklyCycle.week_start_date.desc())
            .all()
        )

        if not cycles:
            return 0

        streak = 0
        expected_week_start = None

        for cycle in cycles:
            # Skip in-progress current week if it hasn't completed yet
            if cycle.week_start_date == current_week_start and cycle.status == WeekStatus.PENDING:
                expected_week_start = cycle.week_start_date - timedelta(days=7)
                continue

            # First completed week evaluated
            if expected_week_start is None:
                # If the latest completed cycle is older than the immediately preceding week, streak broke
                if cycle.week_start_date < current_week_start - timedelta(days=7):
                    break
                expected_week_start = cycle.week_start_date

            # If there is a missing calendar week gap, break streak
            if cycle.week_start_date != expected_week_start:
                break

            if cycle.status == WeekStatus.SUCCESS:
                streak += 1
                expected_week_start = cycle.week_start_date - timedelta(days=7)
            else:
                # FAILED or other non-success status breaks streak
                break

        return streak

    # ── Streak Snapshot ───────────────────────────────────────────────────────

    @staticmethod
    def update_streak_snapshot(
        db: Session, user_id: str, snapshot_date: date
    ) -> StreakSnapshot:
        current_streak = StreakService.calculate_current_streak(db, user_id)

        total_successful_weeks = db.query(WeeklyCycle).filter(
            and_(
                WeeklyCycle.user_id == user_id,
                WeeklyCycle.status  == WeekStatus.SUCCESS,
            )
        ).count()

        total_active_days = (
            db.query(func.count(func.distinct(Workout.workout_date)))
            .filter(Workout.user_id == user_id)
            .scalar() or 0
        )

        snapshot = db.query(StreakSnapshot).filter(
            and_(
                StreakSnapshot.user_id       == user_id,
                StreakSnapshot.snapshot_date == snapshot_date,
            )
        ).first()

        if not snapshot:
            snapshot = StreakSnapshot(user_id=user_id, snapshot_date=snapshot_date)
            db.add(snapshot)

        snapshot.current_streak_weeks   = current_streak
        snapshot.total_successful_weeks = total_successful_weeks
        snapshot.total_active_days      = int(total_active_days)
        snapshot.longest_streak_weeks   = max(
            snapshot.longest_streak_weeks or 0, current_streak
        )
        db.commit()
        db.refresh(snapshot)
        return snapshot

    # ── Avatar Evolution ──────────────────────────────────────────────────────

    @staticmethod
    def check_avatar_evolution(db: Session, user_id: str):
        """
        Evolution rules (daily streak days):
        - Egg       →  Gym Chick  : 30 active days
        - Gym Chick →  Flying Bird: 60 active days
        """
        gam = db.query(UserGamification).filter(
            UserGamification.user_id == user_id
        ).first()

        if not gam:
            gam = UserGamification(user_id=user_id)
            db.add(gam)
            db.commit()
            db.refresh(gam)

        total_active_days = (
            db.query(func.count(func.distinct(Workout.workout_date)))
            .filter(Workout.user_id == user_id)
            .scalar() or 0
        )

        total_successful_weeks = (
            db.query(WeeklyCycle)
            .filter(
                and_(
                    WeeklyCycle.user_id == user_id,
                    WeeklyCycle.status  == WeekStatus.SUCCESS,
                )
            )
            .count()
        )

        gam.total_active_days      = int(total_active_days)
        gam.total_successful_weeks = int(total_successful_weeks)

        # Egg → Gym Chick (30 active days)
        if (
            gam.current_stage == AvatarStage.EGG
            and gam.total_active_days >= 30
        ):
            gam.current_stage        = AvatarStage.BABY_BIRD
            gam.egg_hatched_at       = datetime.utcnow()
            gam.baby_bird_evolved_at = datetime.utcnow()

        # Gym Chick → Flying Bird (60 active days)
        if (
            gam.current_stage == AvatarStage.BABY_BIRD
            and gam.total_active_days >= 60
        ):
            gam.current_stage          = AvatarStage.FLYING_BIRD
            gam.flying_bird_evolved_at = datetime.utcnow()

        db.commit()

    # ── ML: Daily Metrics Upsert ──────────────────────────────────────────────

    @staticmethod
    def _upsert_daily_metrics(
        db: Session, user_id: str, metric_date: date
    ):
        """Aggregate today's volume for ML feature extraction using ORM."""
        result = (
            db.query(
                func.count(func.distinct(WorkoutExercise.id)).label("total_exercises"),
                func.count(WorkoutSet.id).label("total_sets"),
                func.sum(WorkoutSet.reps * WorkoutSet.weight).label("total_volume"),
                func.avg(WorkoutSet.rpe).label("avg_rpe"),
            )
            .select_from(Workout)
            .outerjoin(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
            .outerjoin(WorkoutSet, WorkoutSet.workout_exercise_id == WorkoutExercise.id)
            .filter(
                and_(
                    Workout.user_id == user_id,
                    Workout.workout_date == metric_date,
                )
            )
            .first()
        )

        metrics = db.query(WorkoutMetricsDaily).filter(
            and_(
                WorkoutMetricsDaily.user_id     == user_id,
                WorkoutMetricsDaily.metric_date == metric_date,
            )
        ).first()

        if not metrics:
            metrics = WorkoutMetricsDaily(
                user_id=user_id, metric_date=metric_date
            )
            db.add(metrics)

        if result:
            metrics.total_exercises = result.total_exercises or 0
            metrics.total_sets      = result.total_sets      or 0
            metrics.total_volume    = float(result.total_volume or 0)
            metrics.avg_rpe         = float(result.avg_rpe) if result.avg_rpe else None

        db.commit()

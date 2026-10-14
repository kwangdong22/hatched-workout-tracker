import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DateTime,
    ForeignKey, Numeric, Text, Enum as SAEnum, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import enum


# ── Enums ────────────────────────────────────────────────────────────────────

class WeekStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED  = "failed"
    REST    = "rest"

class AvatarStage(str, enum.Enum):
    EGG         = "egg"
    BABY_BIRD   = "baby_bird"
    FLYING_BIRD = "flying_bird"


# ── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(255), unique=True, nullable=False)
    username      = Column(String(50),  unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    goals          = relationship("WeeklyGoal",      back_populates="user")
    workouts       = relationship("Workout",         back_populates="user")
    weekly_cycles  = relationship("WeeklyCycle",     back_populates="user")
    gamification   = relationship("UserGamification", back_populates="user", uselist=False)


# ── Weekly Goals ─────────────────────────────────────────────────────────────

class WeeklyGoal(Base):
    __tablename__ = "weekly_goals"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id               = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_hours_per_week = Column(Numeric(4, 2), nullable=False)
    target_days_per_week  = Column(Integer, nullable=False)
    started_at            = Column(Date, nullable=False)
    ended_at              = Column(Date, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)

    user          = relationship("User",         back_populates="goals")
    weekly_cycles = relationship("WeeklyCycle",  back_populates="weekly_goal")

    __table_args__ = (
        CheckConstraint("target_days_per_week BETWEEN 1 AND 7"),
    )


# ── Exercises ────────────────────────────────────────────────────────────────

class Exercise(Base):
    __tablename__ = "exercises"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(100), nullable=False)
    muscle_group = Column(String(50))
    equipment    = Column(String(50))
    is_custom    = Column(Boolean, default=False)
    created_by   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


# ── Workouts ─────────────────────────────────────────────────────────────────

class Workout(Base):
    __tablename__ = "workouts"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    routine_id       = Column(UUID(as_uuid=True), nullable=True)
    workout_date     = Column(Date, nullable=False)
    started_at       = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at     = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    user              = relationship("User",             back_populates="workouts")
    workout_exercises = relationship("WorkoutExercise",  back_populates="workout", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "workout_date"),
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id  = Column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    workout  = relationship("Workout",      back_populates="workout_exercises")
    sets     = relationship("WorkoutSet",   back_populates="workout_exercise", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_exercise_id = Column(UUID(as_uuid=True), ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False)
    set_number          = Column(Integer, nullable=False)
    reps                = Column(Integer, nullable=False)
    weight              = Column(Numeric(6, 2), nullable=False)
    rpe                 = Column(Numeric(3, 1), nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)

    workout_exercise = relationship("WorkoutExercise", back_populates="sets")

    __table_args__ = (
        UniqueConstraint("workout_exercise_id", "set_number"),
    )


# ── Weekly Cycles (Streak Tracking) ─────────────────────────────────────────

class WeeklyCycle(Base):
    __tablename__ = "weekly_cycles"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id",        ondelete="CASCADE"), nullable=False)
    weekly_goal_id      = Column(UUID(as_uuid=True), ForeignKey("weekly_goals.id", ondelete="CASCADE"), nullable=False)
    week_start_date     = Column(Date, nullable=False)
    week_end_date       = Column(Date, nullable=False)
    target_days         = Column(Integer, nullable=False)
    completed_days      = Column(Integer, default=0)
    status              = Column(SAEnum(WeekStatus), default=WeekStatus.PENDING)
    auto_rest_enabled   = Column(Boolean, default=False)
    auto_rest_start_date= Column(Date, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user        = relationship("User",       back_populates="weekly_cycles")
    weekly_goal = relationship("WeeklyGoal", back_populates="weekly_cycles")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start_date"),
    )


# ── Streak Snapshots ─────────────────────────────────────────────────────────

class StreakSnapshot(Base):
    __tablename__ = "streak_snapshots"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id               = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot_date         = Column(Date, nullable=False)
    current_streak_weeks  = Column(Integer, default=0)
    longest_streak_weeks  = Column(Integer, default=0)
    total_successful_weeks= Column(Integer, default=0)
    total_active_days     = Column(Integer, default=0)
    created_at            = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date"),
    )


# ── Gamification ─────────────────────────────────────────────────────────────

class UserGamification(Base):
    __tablename__ = "user_gamification"

    user_id                = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    current_stage          = Column(SAEnum(AvatarStage), default=AvatarStage.EGG)
    total_successful_weeks = Column(Integer, default=0)
    total_active_days      = Column(Integer, default=0)
    egg_hatched_at         = Column(DateTime, nullable=True)
    baby_bird_evolved_at   = Column(DateTime, nullable=True)
    flying_bird_evolved_at = Column(DateTime, nullable=True)
    updated_at             = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="gamification")


# ── ML Foundation ────────────────────────────────────────────────────────────

class WorkoutMetricsDaily(Base):
    __tablename__ = "workout_metrics_daily"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric_date      = Column(Date, nullable=False)
    total_volume     = Column(Numeric(10, 2))  # sum of reps * weight
    total_sets       = Column(Integer)
    total_exercises  = Column(Integer)
    avg_rpe          = Column(Numeric(3, 1))
    duration_minutes = Column(Integer)
    created_at       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "metric_date"),
    )


class PredictedFatigue(Base):
    __tablename__ = "predicted_fatigue"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prediction_date  = Column(Date, nullable=False)
    fatigue_score    = Column(Numeric(5, 2))
    confidence       = Column(Numeric(5, 4))
    recommended_rest = Column(Boolean, default=False)
    model_version    = Column(String(50))
    created_at       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "prediction_date"),
    )

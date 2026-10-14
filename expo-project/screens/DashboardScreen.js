import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import AvatarBird from '../components/AvatarBird';
import { workoutAPI, gamificationAPI } from '../services/api';

// ─────────────────────────────────────────────────────────────
//  Replace with real auth token from your auth context/storage
// ─────────────────────────────────────────────────────────────
const MOCK_TOKEN = 'YOUR_AUTH_TOKEN';

export default function DashboardScreen({ navigation }) {
  const [loading, setLoading]           = useState(true);
  const [refreshing, setRefreshing]     = useState(false);
  const [streakData, setStreakData]     = useState(null);
  const [cycleData, setCycleData]       = useState(null);
  const [gamification, setGamification] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [streak, cycle, gam] = await Promise.all([
        workoutAPI.getStreak(MOCK_TOKEN),
        workoutAPI.getWeeklyCycle(MOCK_TOKEN),
        gamificationAPI.getStatus(MOCK_TOKEN),
      ]);
      setStreakData(streak);
      setCycleData(cycle);
      setGamification(gam);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Derive streak days from total_active_days for avatar stage
  const streakDays   = gamification?.total_active_days ?? 0;
  const streakWeeks  = streakData?.current_streak_weeks ?? 0;
  const completedDays = cycleData?.completed_days ?? 0;
  const targetDays   = cycleData?.target_days ?? 3;
  const autoRest     = cycleData?.auto_rest_enabled ?? false;

  if (loading) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator size="large" color="#C4965A" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#C4965A"
        />
      }
    >
      {/* ── Header ───────────────────────────────────────── */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Good morning 👋</Text>
        <Text style={styles.subGreeting}>Here's your progress</Text>
      </View>

      {/* ── Avatar ───────────────────────────────────────── */}
      <AvatarBird streakDays={streakDays} currentStage={gamification?.avatar_stage} />

      {/* ── Stage Label ──────────────────────────────────── */}
      {gamification && (
        <View style={styles.stageTag}>
          <Text style={styles.stageText}>
            {gamification.avatar_stage === 'egg'         && '🥚 Egg Stage'}
            {gamification.avatar_stage === 'baby_bird'   && '🐣 Gym Chick'}
            {gamification.avatar_stage === 'flying_bird' && '🐦 Free Bird'}
          </Text>
        </View>
      )}

      {/* ── Streak Card ──────────────────────────────────── */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Current Streak</Text>
        <Text style={styles.streakNumber}>{streakWeeks}</Text>
        <Text style={styles.streakLabel}>
          {streakWeeks === 1 ? 'week' : 'weeks'} in a row
        </Text>
      </View>

      {/* ── Weekly Progress Card ─────────────────────────── */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>This Week</Text>
        <View style={styles.dotsRow}>
          {Array.from({ length: targetDays }).map((_, i) => (
            <View
              key={i}
              style={[
                styles.dot,
                i < completedDays ? styles.dotFilled : styles.dotEmpty,
              ]}
            />
          ))}
        </View>
        <Text style={styles.weekProgress}>
          {completedDays} / {targetDays} workouts
        </Text>

        {autoRest && (
          <View style={styles.restBadge}>
            <Text style={styles.restBadgeText}>
              ✓ Goal met — rest days won't break your streak
            </Text>
          </View>
        )}
      </View>

      {/* ── Evolution Progress ───────────────────────────── */}
      {gamification && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Evolution Progress</Text>

          <View style={styles.progressRow}>
            <Text style={styles.progressLabel}>Gym Chick (30 days)</Text>
            <Text style={styles.progressValue}>
              {Math.min(streakDays, 30)} / 30
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View
              style={[
                styles.progressBarFill,
                { width: `${Math.min((streakDays / 30) * 100, 100)}%` },
              ]}
            />
          </View>

          <View style={[styles.progressRow, { marginTop: 14 }]}>
            <Text style={styles.progressLabel}>Free Bird (60 days)</Text>
            <Text style={styles.progressValue}>
              {Math.min(streakDays, 60)} / 60
            </Text>
          </View>
          <View style={styles.progressBarBg}>
            <View
              style={[
                styles.progressBarFill,
                styles.progressBarBlue,
                { width: `${Math.min((streakDays / 60) * 100, 100)}%` },
              ]}
            />
          </View>
        </View>
      )}

      {/* ── Log Today CTA ────────────────────────────────── */}
      <TouchableOpacity
        style={styles.ctaButton}
        activeOpacity={0.85}
        onPress={() => navigation?.navigate('Workout')}
      >
        <Text style={styles.ctaText}>Log Today's Workout</Text>
      </TouchableOpacity>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#FAF6F0',
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 40,
    alignItems: 'center',
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Header
  header: {
    width: '100%',
    marginBottom: 8,
  },
  greeting: {
    fontSize: 26,
    fontWeight: '700',
    color: '#4A3728',
    letterSpacing: 0.2,
  },
  subGreeting: {
    fontSize: 15,
    color: '#A09080',
    marginTop: 2,
  },

  // Stage tag
  stageTag: {
    backgroundColor: '#F0E8D8',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 6,
    marginBottom: 20,
  },
  stageText: {
    fontSize: 14,
    color: '#8A6840',
    fontWeight: '600',
  },

  // Cards
  card: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#EDE8E0',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#B0A090',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 10,
    alignSelf: 'flex-start',
  },

  // Streak
  streakNumber: {
    fontSize: 64,
    fontWeight: '800',
    color: '#C4965A',
    lineHeight: 72,
  },
  streakLabel: {
    fontSize: 15,
    color: '#A09080',
    marginTop: 2,
  },

  // Weekly dots
  dotsRow: {
    flexDirection: 'row',
    gap: 10,
    marginVertical: 12,
  },
  dot: {
    width: 18,
    height: 18,
    borderRadius: 9,
  },
  dotFilled: {
    backgroundColor: '#C4965A',
  },
  dotEmpty: {
    backgroundColor: '#EDE8E0',
  },
  weekProgress: {
    fontSize: 14,
    color: '#A09080',
  },
  restBadge: {
    marginTop: 12,
    backgroundColor: '#EDF7ED',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  restBadgeText: {
    fontSize: 12,
    color: '#4A7A50',
    fontWeight: '500',
  },

  // Evolution progress bars
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 13,
    color: '#6A5A4A',
  },
  progressValue: {
    fontSize: 13,
    color: '#A09080',
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    backgroundColor: '#EDE8E0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#F5D76E',
    borderRadius: 4,
  },
  progressBarBlue: {
    backgroundColor: '#7AB4E0',
  },

  // CTA
  ctaButton: {
    width: '100%',
    backgroundColor: '#C4965A',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    marginTop: 8,
  },
  ctaText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});

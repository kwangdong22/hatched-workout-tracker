import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { workoutAPI } from '../services/api';

const MOCK_TOKEN = 'YOUR_AUTH_TOKEN';

const EXERCISES = [
  { id: '1', name: 'Bench Press',    muscle: 'Chest' },
  { id: '2', name: 'Squat',          muscle: 'Legs' },
  { id: '3', name: 'Deadlift',       muscle: 'Back' },
  { id: '4', name: 'Overhead Press', muscle: 'Shoulders' },
  { id: '5', name: 'Pull-Up',        muscle: 'Back' },
  { id: '6', name: 'Barbell Row',    muscle: 'Back' },
];

function SetRow({ setNumber, onSave }) {
  const [reps,   setReps]   = useState('');
  const [weight, setWeight] = useState('');
  const [saved,  setSaved]  = useState(false);

  const handleSave = () => {
    if (!reps || !weight) return;
    const bestScore = parseInt(reps) * parseFloat(weight);
    onSave({ setNumber, reps: parseInt(reps), weight: parseFloat(weight), bestScore });
    setSaved(true);
  };

  return (
    <View style={setStyles.row}>
      <Text style={setStyles.setNum}>Set {setNumber}</Text>
      <TextInput
        style={setStyles.input}
        placeholder="Reps"
        keyboardType="numeric"
        value={reps}
        onChangeText={setReps}
        editable={!saved}
        placeholderTextColor="#C0B8B0"
      />
      <TextInput
        style={setStyles.input}
        placeholder="kg"
        keyboardType="decimal-pad"
        value={weight}
        onChangeText={setWeight}
        editable={!saved}
        placeholderTextColor="#C0B8B0"
      />
      {!saved ? (
        <TouchableOpacity style={setStyles.saveBtn} onPress={handleSave}>
          <Text style={setStyles.saveBtnText}>✓</Text>
        </TouchableOpacity>
      ) : (
        <View style={setStyles.savedTag}>
          <Text style={setStyles.savedTagText}>
            {reps}r × {weight}kg
          </Text>
        </View>
      )}
    </View>
  );
}

export default function WorkoutScreen() {
  const [selectedExercises, setSelectedExercises] = useState([]);
  const [setsMap, setSetsMap]                     = useState({});
  const [logging, setLogging]                     = useState(false);
  const [done, setDone]                           = useState(false);

  const toggleExercise = (ex) => {
    setSelectedExercises((prev) =>
      prev.find((e) => e.id === ex.id)
        ? prev.filter((e) => e.id !== ex.id)
        : [...prev, ex]
    );
  };

  const handleSetSave = (exerciseId, setData) => {
    setSetsMap((prev) => {
      const existingSets = prev[exerciseId] || [];
      const filtered = existingSets.filter((s) => s.setNumber !== setData.setNumber);
      return {
        ...prev,
        [exerciseId]: [...filtered, setData].sort((a, b) => a.setNumber - b.setNumber),
      };
    });
  };

  const handleFinish = async () => {
    if (selectedExercises.length === 0) {
      Alert.alert('No exercises', 'Select at least one exercise.');
      return;
    }
    setLogging(true);
    try {
      // Local calendar date (YYYY-MM-DD)
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const today = `${year}-${month}-${day}`;

      const formattedExercises = selectedExercises.map((ex) => ({
        name: ex.name,
        muscle_group: ex.muscle,
        sets: (setsMap[ex.id] || []).map((s) => ({
          set_number: s.setNumber,
          reps: s.reps,
          weight: s.weight,
        })),
      }));

      const result = await workoutAPI.logWorkout(today, MOCK_TOKEN, formattedExercises);

      if (result.auto_rest_enabled) {
        Alert.alert(
          '🎉 Weekly Goal Met!',
          `You've hit your ${result.target_days}x/week goal. Remaining days are rest days — your streak is safe!`
        );
      } else {
        Alert.alert(
          '✅ Workout Logged',
          `${result.completed_days} / ${result.target_days} workouts this week.`
        );
      }
      setDone(true);
    } catch (err) {
      Alert.alert('Error', err.message);
    } finally {
      setLogging(false);
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Today's Workout</Text>
      <Text style={styles.sub}>Select exercises and log your sets</Text>

      {/* Exercise Picker */}
      <Text style={styles.sectionLabel}>Exercises</Text>
      <View style={styles.exerciseGrid}>
        {EXERCISES.map((ex) => {
          const selected = !!selectedExercises.find((e) => e.id === ex.id);
          return (
            <TouchableOpacity
              key={ex.id}
              style={[styles.exerciseChip, selected && styles.exerciseChipSelected]}
              onPress={() => toggleExercise(ex)}
            >
              <Text style={[styles.exerciseChipText, selected && styles.exerciseChipTextSelected]}>
                {ex.name}
              </Text>
              <Text style={[styles.exerciseChipMuscle, selected && styles.exerciseChipMuscleSelected]}>
                {ex.muscle}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Sets Logger */}
      {selectedExercises.map((ex) => (
        <View key={ex.id} style={styles.exerciseBlock}>
          <Text style={styles.exerciseName}>{ex.name}</Text>
          <Text style={styles.metricHint}>Best score = Reps × Weight</Text>
          {[1, 2, 3, 4].map((setNum) => (
            <SetRow
              key={setNum}
              setNumber={setNum}
              onSave={(data) => handleSetSave(ex.id, data)}
            />
          ))}
          {setsMap[ex.id] && (
            <Text style={styles.bestScore}>
              Best: {Math.max(...setsMap[ex.id].map((s) => s.bestScore)).toFixed(1)} pts
            </Text>
          )}
        </View>
      ))}

      {/* Finish Button */}
      {!done ? (
        <TouchableOpacity
          style={[styles.finishBtn, logging && styles.finishBtnDisabled]}
          onPress={handleFinish}
          disabled={logging}
        >
          {logging
            ? <ActivityIndicator color="#FFF" />
            : <Text style={styles.finishBtnText}>Finish Workout</Text>
          }
        </TouchableOpacity>
      ) : (
        <View style={styles.doneCard}>
          <Text style={styles.doneText}>✅ Workout saved!</Text>
        </View>
      )}
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
    paddingBottom: 60,
  },
  heading: {
    fontSize: 26,
    fontWeight: '700',
    color: '#4A3728',
  },
  sub: {
    fontSize: 14,
    color: '#A09080',
    marginTop: 4,
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#B0A090',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  exerciseGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 28,
  },
  exerciseChip: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#EDE8E0',
    minWidth: 110,
  },
  exerciseChipSelected: {
    backgroundColor: '#C4965A',
    borderColor: '#C4965A',
  },
  exerciseChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4A3728',
  },
  exerciseChipTextSelected: {
    color: '#FFFFFF',
  },
  exerciseChipMuscle: {
    fontSize: 11,
    color: '#A09080',
    marginTop: 2,
  },
  exerciseChipMuscleSelected: {
    color: '#F5E8D4',
  },
  exerciseBlock: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#EDE8E0',
  },
  exerciseName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#4A3728',
    marginBottom: 2,
  },
  metricHint: {
    fontSize: 11,
    color: '#B0A090',
    marginBottom: 14,
    fontStyle: 'italic',
  },
  bestScore: {
    marginTop: 10,
    fontSize: 13,
    fontWeight: '600',
    color: '#C4965A',
    textAlign: 'right',
  },
  finishBtn: {
    backgroundColor: '#C4965A',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    marginTop: 8,
  },
  finishBtnDisabled: {
    opacity: 0.6,
  },
  finishBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  doneCard: {
    backgroundColor: '#EDF7ED',
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    marginTop: 8,
  },
  doneText: {
    color: '#4A7A50',
    fontSize: 15,
    fontWeight: '600',
  },
});

const setStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  setNum: {
    width: 38,
    fontSize: 12,
    color: '#A09080',
    fontWeight: '600',
  },
  input: {
    flex: 1,
    height: 40,
    backgroundColor: '#FAF6F0',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#EDE8E0',
    paddingHorizontal: 10,
    fontSize: 14,
    color: '#4A3728',
    textAlign: 'center',
  },
  saveBtn: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#C4965A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveBtnText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  savedTag: {
    paddingHorizontal: 8,
    paddingVertical: 6,
    backgroundColor: '#F0E8D8',
    borderRadius: 8,
  },
  savedTagText: {
    fontSize: 11,
    color: '#8A6840',
    fontWeight: '600',
  },
});

import React, { useState } from 'react';
import {
  Modal, View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Switch, ActivityIndicator, Alert
} from 'react-native';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useLanguage } from '../i18n/LanguageContext';
import { WorkoutChart } from './WorkoutChart';

interface AddWorkoutModalProps {
  visible: boolean;
  onClose: () => void;
  onWorkoutAdded: () => void;
  microcycleId?: number;
  planId?: number;
  apiUrl: string;
}

export const AddWorkoutModal: React.FC<AddWorkoutModalProps> = ({
  visible,
  onClose,
  onWorkoutAdded,
  microcycleId,
  planId,
  apiUrl
}) => {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [dateStr, setDateStr] = useState(new Date().toISOString().split('T')[0]);
  const [workoutType, setWorkoutType] = useState('Bike');
  const [intensityCategory, setIntensityCategory] = useState('THRESHOLD');
  const [isKeyWorkout, setIsKeyWorkout] = useState(true);
  const [durationMin, setDurationMin] = useState('60');
  const [plannedTss, setPlannedTss] = useState('60');
  const [structure, setStructure] = useState<any>(null);

  const sports = ['Bike', 'Run', 'Swim', 'Strength', 'Rest'];
  const intensities = [
    { key: 'RECOVERY', label: 'Z1 Recovery' },
    { key: 'AEROBIC_BASE', label: 'Z2 Baza' },
    { key: 'TEMPO', label: 'Z3 Tempo' },
    { key: 'THRESHOLD', label: 'Z4 Próg' },
    { key: 'VO2MAX', label: 'Z5 VO2Max' }
  ];

  const handleGenerateAiStructure = () => {
    const dur = parseInt(durationMin) || 60;
    let struct: any = null;

    if (intensityCategory === 'THRESHOLD') {
      struct = {
        name: name || 'Sweet Spot / Threshold',
        blocks: [
          { reps: 1, steps: [{ duration_min: 15, target: 'Z2 60%', label: 'Rozgrzewka' }] },
          { reps: 3, steps: [
            { duration_min: 10, target: 'Z4 95-100%', label: 'Próg' },
            { duration_min: 5, target: 'Z1 50%', label: 'Odpoczynek' }
          ]},
          { reps: 1, steps: [{ duration_min: 15, target: 'Z1 55%', label: 'Wyciszenie' }] }
        ]
      };
      setPlannedTss('70');
    } else if (intensityCategory === 'VO2MAX') {
      struct = {
        name: name || 'VO2Max Intervals',
        blocks: [
          { reps: 1, steps: [{ duration_min: 15, target: 'Z2 65%', label: 'Rozgrzewka' }] },
          { reps: 5, steps: [
            { duration_min: 4, target: 'Z5 115%', label: 'Interwał VO2Max' },
            { duration_min: 4, target: 'Z1 50%', label: 'Regeneracja' }
          ]},
          { reps: 1, steps: [{ duration_min: 10, target: 'Z1 50%', label: 'Wyciszenie' }] }
        ]
      };
      setPlannedTss('80');
    } else {
      struct = {
        name: name || 'Aerobic Endurance',
        blocks: [
          { reps: 1, steps: [{ duration_min: dur, target: 'Z2 65-75%', label: 'Ciągła jazda tlenowa' }] }
        ]
      };
      setPlannedTss(String(Math.round(dur * 0.8)));
    }

    setStructure(struct);
    if (!name) setName(struct.name);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      alert('Podaj nazwę treningu.');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${apiUrl}/plan/workout`, {
        plan_id: planId,
        microcycle_id: microcycleId,
        date: dateStr,
        workout_type: workoutType,
        intensity_category: intensityCategory,
        is_key_workout: isKeyWorkout,
        name: name.trim(),
        planned_duration_minutes: parseInt(durationMin) || 0,
        planned_tss: parseFloat(plannedTss) || 0.0,
        structure: structure
      });

      onWorkoutAdded();
      onClose();
    } catch (e: any) {
      console.error(e);
      alert('Błąd podczas zapisywania treningu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <Text style={styles.title}>{t('add_workout')}</Text>
            <TouchableOpacity onPress={onClose}>
              <MaterialCommunityIcons name="close" size={24} color="#FFF" />
            </TouchableOpacity>
          </View>

          <ScrollView style={{ maxHeight: 500 }}>
            {/* Wybór Sportu */}
            <Text style={styles.label}>{t('sport')}</Text>
            <View style={styles.chipRow}>
              {sports.map(s => (
                <TouchableOpacity
                  key={s}
                  style={[styles.chip, workoutType === s && styles.chipActive]}
                  onPress={() => setWorkoutType(s)}
                >
                  <Text style={[styles.chipText, workoutType === s && styles.chipTextActive]}>{s}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Nazwa Treningu */}
            <Text style={styles.label}>Nazwa treningu</Text>
            <TextInput
              style={styles.input}
              placeholder={t('workout_name_placeholder')}
              placeholderTextColor="#666"
              value={name}
              onChangeText={setName}
            />

            {/* Data i Czas */}
            <View style={styles.row}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.label}>Data (YYYY-MM-DD)</Text>
                <TextInput
                  style={styles.input}
                  value={dateStr}
                  onChangeText={setDateStr}
                />
              </View>
              <View style={{ flex: 1, marginLeft: 8 }}>
                <Text style={styles.label}>{t('duration_min')}</Text>
                <TextInput
                  style={styles.input}
                  keyboardType="numeric"
                  value={durationMin}
                  onChangeText={setDurationMin}
                />
              </View>
            </View>

            {/* Strefa / Kategoria intensywności */}
            <Text style={styles.label}>{t('intensity_type')}</Text>
            <View style={styles.chipRow}>
              {intensities.map(item => (
                <TouchableOpacity
                  key={item.key}
                  style={[styles.chip, intensityCategory === item.key && styles.chipActive]}
                  onPress={() => setIntensityCategory(item.key)}
                >
                  <Text style={[styles.chipText, intensityCategory === item.key && styles.chipTextActive]}>{item.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Switch: Akcent Tygodnia */}
            <View style={[styles.row, { alignItems: 'center', marginVertical: 12 }]}>
              <Text style={{ color: '#CCC', fontSize: 13, flex: 1 }}>{t('key_workout_toggle')}</Text>
              <Switch
                value={isKeyWorkout}
                onValueChange={setIsKeyWorkout}
                trackColor={{ false: '#333', true: '#73E491' }}
              />
            </View>

            {/* Przycisk AI generatora struktury */}
            <TouchableOpacity style={styles.btnAi} onPress={handleGenerateAiStructure}>
              <Text style={styles.btnAiText}>{t('generate_workout_ai')}</Text>
            </TouchableOpacity>

            {/* Podgląd struktury / wykres */}
            {structure && (
              <View style={{ marginTop: 12 }}>
                <Text style={styles.label}>Podgląd struktury (WorkoutChart):</Text>
                <WorkoutChart workoutDoc={structure} />
              </View>
            )}
          </ScrollView>

          {/* Przycisk zapisu */}
          <TouchableOpacity style={styles.btnSave} onPress={handleSave} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#000" />
            ) : (
              <Text style={styles.btnSaveText}>{t('save')}</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    padding: 16
  },
  modalContent: {
    backgroundColor: '#1A1A1D',
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: '#333'
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14
  },
  title: {
    color: '#FFF',
    fontSize: 17,
    fontWeight: 'bold'
  },
  label: {
    color: '#888',
    fontSize: 11,
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 6
  },
  input: {
    backgroundColor: '#26262B',
    color: '#FFF',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    borderWidth: 1,
    borderColor: '#38383F'
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6
  },
  chip: {
    backgroundColor: '#26262B',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#38383F'
  },
  chipActive: {
    backgroundColor: '#4DA8DA',
    borderColor: '#4DA8DA'
  },
  chipText: {
    color: '#CCC',
    fontSize: 11
  },
  chipTextActive: {
    color: '#000',
    fontWeight: 'bold'
  },
  btnAi: {
    backgroundColor: '#2C2C30',
    borderWidth: 1,
    borderColor: '#73E491',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 14
  },
  btnAiText: {
    color: '#73E491',
    fontWeight: 'bold',
    fontSize: 12
  },
  btnSave: {
    backgroundColor: '#73E491',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16
  },
  btnSaveText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 13
  }
});

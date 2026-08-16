import React, { useState } from 'react';
import {
  Modal, View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, ActivityIndicator
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import { useLanguage } from '../i18n/LanguageContext';

interface GenerateMicrocycleModalProps {
  visible: boolean;
  onClose: () => void;
  onGenerated: () => void;
  userId: number;
  goals: any[];
  apiUrl: string;
}

export const GenerateMicrocycleModal: React.FC<GenerateMicrocycleModalProps> = ({
  visible,
  onClose,
  onGenerated,
  userId,
  goals,
  apiUrl
}) => {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [targetTss, setTargetTss] = useState('420');
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(
    goals && goals.length > 0 ? goals[0].id : null
  );
  const [focus, setFocus] = useState('');

  const handleGenerate = async () => {
    setLoading(true);
    try {
      await axios.post(`${apiUrl}/plan/microcycle/generate`, {
        user_id: userId,
        target_tss: parseFloat(targetTss) || 400.0,
        goal_id: selectedGoalId,
        focus: focus.trim() || undefined
      });

      onGenerated();
      onClose();
    } catch (e: any) {
      console.error(e);
      alert('Nie udało się wygenerować mikrocyklu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <Text style={styles.title}>🪄 {t('plan_microcycle_ai')}</Text>
            <TouchableOpacity onPress={onClose}>
              <MaterialCommunityIcons name="close" size={24} color="#FFF" />
            </TouchableOpacity>
          </View>

          <ScrollView style={{ maxHeight: 420 }}>
            {/* Wybór Celu */}
            <Text style={styles.label}>Powiązany cel startowy</Text>
            <View style={styles.chipRow}>
              {goals && goals.length > 0 ? (
                goals.map(g => (
                  <TouchableOpacity
                    key={g.id}
                    style={[styles.chip, selectedGoalId === g.id && styles.chipActive]}
                    onPress={() => setSelectedGoalId(g.id)}
                  >
                    <Text style={[styles.chipText, selectedGoalId === g.id && styles.chipTextActive]}>
                      {g.priority} • {g.event_name || g.name}
                    </Text>
                  </TouchableOpacity>
                ))
              ) : (
                <Text style={{ color: '#888', fontSize: 12 }}>Brak zdefiniowanych celów.</Text>
              )}
            </View>

            {/* Docelowy TSS */}
            <Text style={styles.label}>{t('target_tss_label')}</Text>
            <TextInput
              style={styles.input}
              keyboardType="numeric"
              value={targetTss}
              onChangeText={setTargetTss}
              placeholder="np. 450"
              placeholderTextColor="#666"
            />

            {/* Fokus tygodnia */}
            <Text style={styles.label}>Główny fokus / uwaga do mikrocyklu (opcjonalnie)</Text>
            <TextInput
              style={[styles.input, { height: 60, textAlignVertical: 'top' }]}
              multiline
              value={focus}
              onChangeText={setFocus}
              placeholder="np. Rozbudowa SweetSpot pod wyścig górski, regeneracja w piątek"
              placeholderTextColor="#666"
            />
          </ScrollView>

          <TouchableOpacity style={styles.btnGenerate} onPress={handleGenerate} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#000" />
            ) : (
              <Text style={styles.btnGenerateText}>🪄 GENERUJ MIKROCYKL</Text>
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
    fontSize: 16,
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
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 6
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
    backgroundColor: '#73E491',
    borderColor: '#73E491'
  },
  chipText: {
    color: '#CCC',
    fontSize: 11
  },
  chipTextActive: {
    color: '#000',
    fontWeight: 'bold'
  },
  btnGenerate: {
    backgroundColor: '#73E491',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16
  },
  btnGenerateText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 13
  }
});

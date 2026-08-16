import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, Modal, 
  ScrollView, Switch, Alert, StyleSheet, Dimensions 
} from 'react-native';
import { X, Calendar as CalendarIcon, Flag, Target, ChevronDown } from 'lucide-react-native';
import { useLanguage } from './i18n/LanguageContext';
import { API_URL } from './config';

interface GoalFormProps {
  isVisible: boolean;
  onClose: () => void;
  userId: number;
}

const screenHeight = Dimensions.get('window').height;

export default function AddGoalModal({ isVisible, onClose, userId }: GoalFormProps) {
  const { t } = useLanguage();
  const [form, setForm] = useState({
    discipline: t('bike'),
    priority: 'A',
    event_name: '',
    event_type: '',
    event_date: new Date().toISOString().split('T')[0],
    is_recreational: false
  });

  const disciplines = [t('bike'), t('run'), t('swim'), t('triathlon')];
  const priorities = ['A', 'B', 'C'];

  const handleSave = async () => {
    if (!form.event_name || !form.event_type || !form.event_date) {
      Alert.alert(t('error'), t('fill_all_fields_error'));
      return;
    }

    try {
      const response = await fetch(`${API_URL}/goals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ...form
        }),
      });

      if (response.ok) {
        Alert.alert(t('success'), t('goal_added_success'));
        onClose();
      }
    } catch (error) {
      Alert.alert(t('error'), t('conn_error_goal'));
    }
  };

  return (
    <Modal visible={isVisible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.modalContent}>
          
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>{t('new_goal')}</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X color="white" size={20} />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            
            {/* Wybór Dyscypliny */}
            <Text style={styles.label}>{t('discipline')}</Text>
            <View style={styles.disciplineRow}>
              {disciplines.map(d => (
                <TouchableOpacity 
                  key={d}
                  onPress={() => setForm({...form, discipline: d})}
                  style={[
                    styles.disciplineBtn,
                    { 
                      backgroundColor: form.discipline === d ? '#22C55E' : '#1E293B',
                      borderColor: form.discipline === d ? '#22C55E' : '#334155'
                    }
                  ]}
                >
                  <Text style={{ 
                    fontWeight: 'bold', 
                    color: form.discipline === d ? 'black' : '#CBD5E1' 
                  }}>{d}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Wybór Priorytetu */}
            <Text style={styles.label}>{t('priority')}</Text>
            <View style={styles.priorityRow}>
              {priorities.map(p => (
                <TouchableOpacity 
                  key={p}
                  onPress={() => setForm({...form, priority: p})}
                  style={[
                    styles.priorityBtn,
                    { 
                      borderColor: form.priority === p ? '#22C55E' : '#334155',
                      backgroundColor: form.priority === p ? 'rgba(34, 197, 94, 0.1)' : '#1E293B'
                    }
                  ]}
                >
                  <Text style={{ 
                    fontWeight: '900', 
                    fontSize: 18,
                    color: form.priority === p ? '#22C55E' : '#64748B' 
                  }}>{p}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={{ marginBottom: 24 }}>
              <View style={{ marginBottom: 16 }}>
                <Text style={styles.label}>{t('race_name')}</Text>
                <TextInput 
                  placeholder={t('race_name_placeholder')}
                  placeholderTextColor="#475569"
                  style={styles.input}
                  value={form.event_name}
                  onChangeText={(t) => setForm({...form, event_name: t})}
                />
              </View>

              <View>
                <Text style={styles.label}>{t('distance_type')}</Text>
                <TextInput 
                  placeholder={t('distance_placeholder')}
                  placeholderTextColor="#475569"
                  style={styles.input}
                  value={form.event_type}
                  onChangeText={(t) => setForm({...form, event_type: t})}
                />
              </View>

              <View>
                <Text style={styles.label}>{t('event_date')}</Text>
                <TextInput 
                  placeholder="YYYY-MM-DD"
                  placeholderTextColor="#475569"
                  style={styles.input}
                  value={form.event_date}
                  onChangeText={(t) => setForm({...form, event_date: t})}
                  // @ts-ignore - works on web
                  type="date"
                />
                <Text style={{ color: '#475569', fontSize: 10, marginTop: 4 }}>Format: RRRR-MM-DD</Text>
              </View>
            </View>

            {/* Data i Przełącznik */}
            <View style={styles.switchRow}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={styles.iconBox}>
                  <Flag color="#22c55e" size={18} />
                </View>
                <Text style={{ color: 'white', fontWeight: '500' }}>{t('recreational_start')}</Text>
              </View>
              <Switch 
                value={form.is_recreational}
                onValueChange={(v) => setForm({...form, is_recreational: v})}
                trackColor={{ false: "#334155", true: "#22c55e" }}
              />
            </View>

            {/* Przycisk Akcji */}
            <TouchableOpacity 
              onPress={handleSave}
              style={styles.saveBtn}
            >
              <Text style={styles.saveBtnText}>{t('save_goal')}</Text>
            </TouchableOpacity>

            <View style={{ height: 80 }} />
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end'
  },
  modalContent: {
    backgroundColor: '#0F172A',
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    padding: 24,
    height: screenHeight * 0.85,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 32
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold'
  },
  closeBtn: {
    backgroundColor: '#1E293B',
    padding: 8,
    borderRadius: 20
  },
  label: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 12,
    marginLeft: 4
  },
  disciplineRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24
  },
  disciplineBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1
  },
  priorityRow: {
    flexDirection: 'row',
    marginBottom: 24
  },
  priorityBtn: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 24,
    marginRight: 16,
    borderWidth: 2
  },
  input: {
    backgroundColor: '#1E293B',
    color: 'white',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
    fontWeight: '500'
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    padding: 16,
    borderRadius: 16,
    marginBottom: 32,
    borderWidth: 1,
    borderColor: '#1E293B'
  },
  iconBox: {
    backgroundColor: '#334155',
    padding: 8,
    borderRadius: 8,
    marginRight: 12
  },
  saveBtn: {
    backgroundColor: '#22C55E',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center'
  },
  saveBtnText: {
    color: 'black',
    fontWeight: '900',
    fontSize: 18
  }
});
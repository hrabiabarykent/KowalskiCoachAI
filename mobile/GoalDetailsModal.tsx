import React, { useState } from 'react';
import { 
  View, Text, TouchableOpacity, Modal, 
  ScrollView, ActivityIndicator, Alert, StyleSheet, Dimensions 
} from 'react-native';
import { X, Target, CalendarDays, Brain, Trash2, Clock } from 'lucide-react-native';
import axios from 'axios';
import { useLanguage } from './i18n/LanguageContext';

interface GoalDetailsModalProps {
  isVisible: boolean;
  onClose: () => void;
  goal: any;
  apiUrl: string;
  onGoalUpdated: () => void;
  onDelete: (goalId: number) => void;
}

const screenHeight = Dimensions.get('window').height;

export default function GoalDetailsModal({ isVisible, onClose, goal, apiUrl, onGoalUpdated, onDelete }: GoalDetailsModalProps) {
  const { t } = useLanguage();
  const [evaluating, setEvaluating] = useState(false);

  if (!goal) return null;

  const calculateWeeksLeft = (targetDateStr: string) => {
    const target = new Date(targetDateStr);
    const today = new Date();
    const diffTime = target.getTime() - today.getTime();
    if (diffTime < 0) return 0;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, Math.round(diffDays / 7));
  };

  const weeksLeft = calculateWeeksLeft(goal.date);

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'A': return '#EF4444';
      case 'B': return '#F97316';
      case 'C': return '#3B82F6';
      default: return '#64748B';
    }
  };

  const handleEvaluate = async () => {
    try {
      setEvaluating(true);
      const res = await axios.post(`${apiUrl}/evaluate-goal/${goal.id}`);
      if (res.data.status === 'success') {
        onGoalUpdated();
      }
    } catch (error) {
      console.error(error);
      Alert.alert(t('error'), t('conn_error'));
    } finally {
      setEvaluating(false);
    }
  };

  const handleDelete = () => {
    const goalId = goal.id;
    onClose();
    // Let the parent handle the delete
    onDelete(goalId);
  };

  return (
    <Modal visible={isVisible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.modalContent}>
          
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(goal.priority) }]}>
                <Text style={styles.priorityText}>{goal.priority}</Text>
              </View>
              <Text style={styles.headerTitle}>{t('goal_details')}</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X color="white" size={20} />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} style={styles.scroll}>
            
            {/* Main Info Card */}
            <View style={styles.card}>
              <View style={styles.infoRow}>
                <Target color="#4DA8DA" size={24} style={{ marginRight: 12 }} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.goalTitle} numberOfLines={2}>{goal.name}</Text>
                  <Text style={styles.goalType}>{goal.type}</Text>
                </View>
              </View>

              <View style={styles.divider} />

              <View style={styles.metaRow}>
                <View style={styles.metaItem}>
                  <CalendarDays color="#a8b2d1" size={18} style={{ marginRight: 8 }} />
                  <Text style={styles.metaText}>{goal.date}</Text>
                </View>
                <View style={styles.weeksBadge}>
                  <Clock color="#a8b2d1" size={14} style={{ marginRight: 8 }} />
                  <Text style={[styles.metaText, { fontSize: 12, fontWeight: '700' }]}>{weeksLeft} {t('weeks_left')}</Text>
                </View>
              </View>
            </View>

            {/* Evaluation Section */}
            <View style={styles.evalSection}>
              <View style={styles.sectionHeader}>
                <Brain color="#22c55e" size={20} />
                <Text style={styles.sectionTitle}>{t('ai_evaluation')}</Text>
              </View>

              {goal.ai_evaluation ? (
                <View style={styles.evalBody}>
                  <Text style={styles.evalText}>{goal.ai_evaluation}</Text>
                </View>
              ) : (
                <View style={styles.emptyEval}>
                  <Text style={styles.emptyText}>{t('no_evaluation')}</Text>
                  
                  <TouchableOpacity 
                    onPress={handleEvaluate}
                    disabled={evaluating}
                    style={[styles.evalBtn, { backgroundColor: evaluating ? '#334155' : '#16A34A' }]}
                  >
                    {evaluating ? (
                      <ActivityIndicator size="small" color="#fff" style={{ marginRight: 8 }} />
                    ) : (
                      <Brain color="#fff" size={18} style={{ marginRight: 8 }} />
                    )}
                    <Text style={styles.btnText}>{evaluating ? t('evaluating') : t('evaluate_goal')}</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>

            <View style={{ height: 40 }} />
          </ScrollView>

          {/* Footer Actions */}
          <View style={styles.footer}>
            <TouchableOpacity 
              onPress={handleDelete}
              style={styles.deleteBtn}
            >
              <Trash2 color="#ef4444" size={20} />
              <Text style={styles.deleteText}>{t('delete_goal')}</Text>
            </TouchableOpacity>
          </View>

        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end'
  },
  modalContent: {
    backgroundColor: '#0F172A', // slate-900
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 24,
    height: screenHeight * 0.85,
    borderTopWidth: 1,
    borderTopColor: '#1E293B', // slate-800
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  priorityBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12
  },
  priorityText: {
    color: 'white',
    fontWeight: 'bold'
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
  scroll: {
    flex: 1
  },
  card: {
    backgroundColor: '#1E293B',
    padding: 20,
    borderRadius: 20,
    marginBottom: 24
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16
  },
  goalTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1
  },
  goalType: {
    color: '#94A3B8', // slate-400
    textTransform: 'capitalize',
    marginTop: 4
  },
  divider: {
    height: 1,
    backgroundColor: '#334155', // slate-700
    width: '100%',
    marginBottom: 16
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  metaText: {
    color: '#CBD5E1', // slate-300
    fontWeight: '500'
  },
  weeksBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(51, 65, 85, 0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 99
  },
  evalSection: {
    marginBottom: 24
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16
  },
  sectionTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8
  },
  evalBody: {
    backgroundColor: 'rgba(30, 41, 59, 0.8)',
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#334155'
  },
  evalText: {
    color: '#CBD5E1',
    lineHeight: 24
  },
  emptyEval: {
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    padding: 24,
    borderRadius: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    borderStyle: 'dashed'
  },
  emptyText: {
    color: '#94A3B8',
    textAlign: 'center',
    marginBottom: 16
  },
  evalBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12
  },
  btnText: {
    color: 'white',
    fontWeight: 'bold'
  },
  footer: {
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#1E293B'
  },
  deleteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)'
  },
  deleteText: {
    color: '#EF4444',
    fontWeight: 'bold',
    marginLeft: 8
  }
});

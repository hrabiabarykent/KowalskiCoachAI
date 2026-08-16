import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons, Feather, Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../i18n/LanguageContext';

interface MicrocycleTimelineProps {
  microcycle: any;
  onGeneratePress: () => void;
  onAddWorkoutPress: () => void;
  onSyncIntervalsPress: () => void;
  syncing: boolean;
}

export const MicrocycleTimeline: React.FC<MicrocycleTimelineProps> = ({
  microcycle,
  onGeneratePress,
  onAddWorkoutPress,
  onSyncIntervalsPress,
  syncing
}) => {
  const { t } = useLanguage();

  if (!microcycle) {
    return (
      <View style={styles.emptyCard}>
        <MaterialCommunityIcons name="calendar-sync" size={32} color="#4DA8DA" style={{ marginBottom: 8 }} />
        <Text style={styles.emptyTitle}>{t('microcycle')}</Text>
        <Text style={styles.emptySubtitle}>Brak aktywnego mikrocyklu na ten okres.</Text>
        <TouchableOpacity style={styles.btnPrimary} onPress={onGeneratePress}>
          <Text style={styles.btnPrimaryText}>🪄 {t('plan_microcycle_ai')}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const targetTss = microcycle.target_tss || 0;
  const plannedTss = microcycle.total_planned_tss || 0;
  const progressPercent = targetTss > 0 ? Math.min(100, Math.round((plannedTss / targetTss) * 100)) : 0;

  return (
    <View style={styles.container}>
      {/* Header mikrocyklu */}
      <View style={styles.headerRow}>
        <View>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={styles.weekBadge}>W{microcycle.week_number}</Text>
            <Text style={styles.phaseText}>{microcycle.phase} • {microcycle.start_date} - {microcycle.end_date}</Text>
          </View>
          {microcycle.goal_name && (
            <Text style={styles.goalText}>🎯 {microcycle.goal_name}</Text>
          )}
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={styles.tssProgressText}>{Math.round(plannedTss)} / {Math.round(targetTss)} TSS</Text>
          <Text style={styles.tssPercentText}>{progressPercent}% celu</Text>
        </View>
      </View>

      {/* Pasek postępu TSS */}
      <View style={styles.progressBarBg}>
        <View style={[styles.progressBarFill, { width: `${progressPercent}%` }]} />
      </View>

      {microcycle.focus && (
        <Text style={styles.focusText}>💡 {microcycle.focus}</Text>
      )}

      {/* Przyciski akcji */}
      <View style={styles.actionsRow}>
        <TouchableOpacity style={styles.actionBtnSecondary} onPress={onAddWorkoutPress}>
          <Ionicons name="add-circle-outline" size={16} color="#4DA8DA" />
          <Text style={styles.actionBtnSecondaryText}>{t('add_workout')}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionBtnPrimary} onPress={onGeneratePress}>
          <Text style={styles.actionBtnPrimaryText}>🪄 AI Plan</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionBtnSync} onPress={onSyncIntervalsPress} disabled={syncing}>
          <MaterialCommunityIcons name="cloud-upload-outline" size={16} color="#FFF" />
          <Text style={styles.actionBtnSyncText}>{syncing ? '...' : 'Intervals'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1E1E24',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333'
  },
  emptyCard: {
    backgroundColor: '#1E1E24',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333'
  },
  emptyTitle: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  emptySubtitle: {
    color: '#888',
    fontSize: 12,
    marginBottom: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10
  },
  weekBadge: {
    backgroundColor: '#4DA8DA',
    color: '#000',
    fontWeight: 'bold',
    fontSize: 11,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8
  },
  phaseText: {
    color: '#CCC',
    fontSize: 12,
    fontWeight: '600'
  },
  goalText: {
    color: '#73E491',
    fontSize: 11,
    marginTop: 4
  },
  tssProgressText: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: 'bold'
  },
  tssPercentText: {
    color: '#888',
    fontSize: 10
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#2C2C30',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#73E491',
    borderRadius: 3
  },
  focusText: {
    color: '#AAA',
    fontSize: 11,
    fontStyle: 'italic',
    marginBottom: 12
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8
  },
  btnPrimary: {
    backgroundColor: '#73E491',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8
  },
  btnPrimaryText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 12
  },
  actionBtnSecondary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2C2C30',
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4
  },
  actionBtnSecondaryText: {
    color: '#4DA8DA',
    fontSize: 11,
    fontWeight: 'bold'
  },
  actionBtnPrimary: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3E505B',
    paddingVertical: 8,
    borderRadius: 8
  },
  actionBtnPrimaryText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold'
  },
  actionBtnSync: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0F52BA',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4
  },
  actionBtnSyncText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold'
  }
});

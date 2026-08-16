import React from 'react';
import {
  ScrollView, View, Text, StyleSheet, RefreshControl, Dimensions, TouchableOpacity, ActivityIndicator
} from 'react-native';
import { MaterialCommunityIcons, Ionicons, Feather } from '@expo/vector-icons';
import { Svg, Rect, Text as SvgText, Line } from 'react-native-svg';
import { useLanguage } from '../i18n/LanguageContext';
import { MicrocycleTimeline } from '../components/MicrocycleTimeline';
import { TrainingPlanData, TrainingGoal, PlannedWorkout } from '../types';

const screenWidth = Dimensions.get("window").width;

interface PlanScreenProps {
  planData: TrainingPlanData | null;
  loadingPlan: boolean;
  onRefreshPlan: () => void;
  goals: TrainingGoal[];
  atpData: any;
  loadingAtp: boolean;
  onGenerateATP: () => void;
  onResetAtpData: () => void;
  onApprovePlan: (planId: number) => void;
  onRejectPlan: (planId: number) => void;
  onSelectWorkout: (workout: PlannedWorkout) => void;
  onSelectGoalDetails: (goal: TrainingGoal) => void;
  onOpenAddGoal: () => void;
  onOpenAddWorkout: () => void;
  onOpenGenerateMicrocycle: () => void;
  onSyncIntervals: () => void;
  syncingIntervals: boolean;
}

export const PlanScreen: React.FC<PlanScreenProps> = ({
  planData,
  loadingPlan,
  onRefreshPlan,
  goals,
  atpData,
  loadingAtp,
  onGenerateATP,
  onResetAtpData,
  onApprovePlan,
  onRejectPlan,
  onSelectWorkout,
  onSelectGoalDetails,
  onOpenAddGoal,
  onOpenAddWorkout,
  onOpenGenerateMicrocycle,
  onSyncIntervals,
  syncingIntervals
}) => {
  const { t } = useLanguage();
  const activeMicrocycle = planData?.microcycles?.[0];

  return (
    <ScrollView
      contentContainerStyle={styles.scroll}
      refreshControl={<RefreshControl refreshing={loadingPlan} onRefresh={onRefreshPlan} tintColor="#FFF" />}
    >
      {/* Microcycle Timeline */}
      <MicrocycleTimeline
        microcycle={activeMicrocycle}
        onGeneratePress={onOpenGenerateMicrocycle}
        onAddWorkoutPress={onOpenAddWorkout}
        onSyncIntervalsPress={onSyncIntervals}
        syncing={syncingIntervals}
      />

      {/* Plan Status & Approval */}
      {!planData || !planData.has_plan ? (
        <View style={styles.card}>
          <Text style={{ color: '#888', textAlign: 'center' }}>{t('no_active_plan')}</Text>
        </View>
      ) : (
        <View>
          {planData.plan?.status === 'PENDING_APPROVAL' && (
            <View style={[styles.card, { borderColor: '#F6B352', borderWidth: 1 }]}>
              <View style={styles.row}>
                <Ionicons name="warning" size={20} color="#F6B352" />
                <Text style={[styles.cardTitle, { marginBottom: 0, marginLeft: 8, color: '#F6B352' }]}>
                  {t('plan_needs_approval')}
                </Text>
              </View>
              <Text style={{ color: '#CCC', marginVertical: 10 }}>{t('plan_approval_desc')}</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 }}>
                <TouchableOpacity
                  style={[styles.btnMain, { flex: 0.48, backgroundColor: '#2C2C30' }]}
                  onPress={() => planData.plan?.id && onRejectPlan(planData.plan.id)}
                >
                  <Text style={{ color: '#FFF', fontWeight: 'bold', textAlign: 'center' }}>{t('reject')}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btnMain, { flex: 0.48, backgroundColor: '#73E491' }]}
                  onPress={() => planData.plan?.id && onApprovePlan(planData.plan.id)}
                >
                  <Text style={{ color: '#000', fontWeight: 'bold', textAlign: 'center' }}>{t('accept')}</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Workouts List */}
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 10, marginBottom: 10 }}>
            <Text style={styles.sectionTitle}>{t('upcoming_workouts')} ({planData.plan?.current_phase || 'Base'})</Text>
            <TouchableOpacity
              style={styles.btnAddSmall}
              onPress={onOpenAddWorkout}
            >
              <Text style={{ color: '#73E491', fontSize: 11, fontWeight: 'bold' }}>+ {t('add_workout')}</Text>
            </TouchableOpacity>
          </View>

          {planData.workouts?.map((workout, idx) => {
            const isProposed = workout.status === 'PROPOSED' || workout.status === 'Proposed';
            const isKey = workout.is_key_workout;
            return (
              <TouchableOpacity
                key={idx}
                style={[
                  styles.workoutCard,
                  isProposed && { borderColor: '#F6B352', borderWidth: 1 },
                  isKey && { borderLeftColor: '#F23661', borderLeftWidth: 4 },
                  workout.source === 'intervals' && { borderLeftColor: workout.color || '#4DA8DA', borderLeftWidth: 4 }
                ]}
                onPress={() => onSelectWorkout(workout)}
              >
                <View style={styles.row}>
                  <Text style={styles.workoutDate}>{workout.date}</Text>
                  <View style={{ flexDirection: 'row', gap: 4, marginLeft: 'auto' }}>
                    {isKey && (
                      <Text style={[styles.proposedBadge, { backgroundColor: '#F23661', color: '#FFF' }]}>🔥 {t('accent')}</Text>
                    )}
                    {workout.intensity_category && workout.intensity_category !== 'AEROBIC_BASE' && (
                      <Text style={[styles.proposedBadge, { backgroundColor: '#2C2C30', color: '#AAA' }]}>{workout.intensity_category}</Text>
                    )}
                    {isProposed && <Text style={styles.proposedBadge}>{t('proposed')}</Text>}
                    {workout.source === 'intervals' && <Text style={[styles.proposedBadge, { backgroundColor: workout.color || '#4DA8DA' }]}>{t('calendar')}</Text>}
                  </View>
                </View>
                <Text style={styles.workoutName}>{workout.name}</Text>
                <View style={styles.row}>
                  <Text style={styles.workoutStat}><Ionicons name="time-outline" size={14} /> {workout.planned_duration_minutes} min</Text>
                  <Text style={[styles.workoutStat, { marginLeft: 15 }]}><Feather name="activity" size={14} /> {workout.planned_tss} TSS</Text>
                  <Text style={[styles.workoutStat, { marginLeft: 15, color: '#888' }]}>{workout.workout_type}</Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      )}

      {/* Goals List */}
      <View style={{ marginTop: 20 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <Text style={styles.sectionTitle}>{t('my_goals')}</Text>
          <TouchableOpacity
            style={{ backgroundColor: '#22C55E', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8 }}
            onPress={onOpenAddGoal}
          >
            <Text style={{ color: '#000', fontWeight: 'bold', fontSize: 12 }}>+ {t('add_goal')}</Text>
          </TouchableOpacity>
        </View>
        {goals && goals.length > 0 ? (
          goals.map((g, i) => {
            const isAmbitious = g.ai_evaluation && g.ai_evaluation.toLowerCase().includes('ambitny');
            return (
              <TouchableOpacity
                key={i}
                style={[styles.workoutCard, { borderLeftColor: isAmbitious ? '#F23661' : '#7DBB5E', borderLeftWidth: 4 }]}
                onPress={() => onSelectGoalDetails(g)}
              >
                <View style={styles.row}>
                  <Text style={styles.workoutDate}>{g.event_date}</Text>
                  <Text style={[styles.proposedBadge, { backgroundColor: g.priority === 'A' ? '#EB5150' : '#4DA8DA', color: '#FFF' }]}>
                    Priority {g.priority}
                  </Text>
                </View>
                <Text style={styles.workoutName}>{g.event_name}</Text>
                <Text style={styles.workoutStat}>{g.event_type || g.discipline}</Text>
              </TouchableOpacity>
            );
          })
        ) : (
          <View style={[styles.card, { alignItems: 'center', paddingVertical: 25 }]}>
            <Text style={{ color: '#888', textAlign: 'center' }}>Brak zdefiniowanych celów.</Text>
          </View>
        )}
      </View>

      {/* ATP Section */}
      <View style={[styles.card, { marginTop: 20 }]}>
        <View style={styles.row}>
          <Text style={styles.cardTitle}>
            <MaterialCommunityIcons name="calendar-star" size={18} color="#4DA8DA" /> {t('annual_training_plan')}
          </Text>
        </View>

        {!atpData ? (
          <TouchableOpacity style={styles.btnMain} onPress={onGenerateATP} disabled={loadingAtp}>
            {loadingAtp ? (
              <View style={{ alignItems: 'center' }}>
                <ActivityIndicator color="#000" />
                <Text style={{ color: '#000', fontSize: 10, marginTop: 5 }}>{t('atp_generating')}</Text>
              </View>
            ) : (
              <Text style={styles.btnText}>{t('generate_atp')}</Text>
            )}
          </TouchableOpacity>
        ) : atpData.type === 'structured' && atpData.data?.weeks ? (
          <View>
            {/* CTL Projection Chart using SVG */}
            {(() => {
              const weeks = atpData.data.weeks;
              const mesocycles = atpData.data.mesocycles || [];
              const goalsTimeline = atpData.data.goals_timeline || [];
              const ctlValues = weeks.map((w: any) => w.projected_ctl || 0);
              const maxCTL = Math.max(...ctlValues, 1) * 1.15;
              const minCTL = Math.max(0, Math.min(...ctlValues) - 10);
              const chartW = screenWidth - 80;
              const chartH = 180;
              const barW = chartW / Math.max(weeks.length, 1);

              const getWeekColor = (weekNum: number) => {
                const meso = mesocycles.find((m: any) => weekNum >= m.start_week && weekNum <= m.end_week);
                return meso?.color || '#2C2C30';
              };

              return (
                <View style={{ marginTop: 10 }}>
                  <Text style={{ color: '#888', fontSize: 11, fontWeight: 'bold', marginBottom: 10 }}>{t('projected_ctl')}</Text>
                  <View style={{ alignItems: 'center' }}>
                    <Svg width={chartW} height={chartH}>
                      {weeks.map((w: any, idx: number) => {
                        const ctlNorm = (w.projected_ctl - minCTL) / Math.max((maxCTL - minCTL), 1);
                        const barH = Math.max(4, ctlNorm * (chartH - 25));
                        const x = idx * barW;
                        const y = chartH - 20 - barH;
                        return (
                          <Rect
                            key={idx}
                            x={x + 1}
                            y={y}
                            width={Math.max(1, barW - 2)}
                            height={barH}
                            fill={getWeekColor(w.week_number)}
                            opacity={0.85}
                            rx={2}
                          />
                        );
                      })}
                      {goalsTimeline.map((g: any, idx: number) => {
                        const wx = Math.min(g.week_number - 1, weeks.length - 1);
                        const x = wx * barW + barW / 2;
                        return (
                          <React.Fragment key={`goal-${idx}`}>
                            <Line x1={x} y1={0} x2={x} y2={chartH - 20} stroke={g.priority === 'A' ? '#EB5150' : '#F6B352'} strokeWidth={2} strokeDasharray="4 3" />
                            <SvgText x={x} y={10} fill={g.priority === 'A' ? '#EB5150' : '#F6B352'} fontSize="7" textAnchor="middle" fontWeight="bold">
                              {g.priority}
                            </SvgText>
                          </React.Fragment>
                        );
                      })}
                    </Svg>
                  </View>

                  {/* Mesocycle Legend */}
                  <Text style={{ color: '#888', fontSize: 11, fontWeight: 'bold', marginTop: 15, marginBottom: 8 }}>{t('mesocycle_legend')}</Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
                    {mesocycles.map((m: any, idx: number) => (
                      <View key={idx} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 12, marginBottom: 6 }}>
                        <View style={{ width: 12, height: 12, borderRadius: 3, backgroundColor: m.color, marginRight: 6 }} />
                        <Text style={{ color: '#CCC', fontSize: 11 }}>{m.name}</Text>
                      </View>
                    ))}
                  </View>

                  <TouchableOpacity style={[styles.btnMain, { marginTop: 20, backgroundColor: '#2C2C30' }]} onPress={onResetAtpData}>
                    <Text style={{ color: '#FFF', fontWeight: 'bold' }}>↻ {t('generate_atp')}</Text>
                  </TouchableOpacity>
                </View>
              );
            })()}
          </View>
        ) : (
          <View>
            <Text style={styles.insightText}>{atpData.data || JSON.stringify(atpData)}</Text>
            <TouchableOpacity style={[styles.btnMain, { marginTop: 15, backgroundColor: '#2C2C30' }]} onPress={onResetAtpData}>
              <Text style={{ color: '#FFF', fontWeight: 'bold' }}>↻ {t('generate_atp')}</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scroll: { paddingBottom: 100, padding: 15 },
  card: { backgroundColor: '#1A1A1D', borderRadius: 12, padding: 20, marginBottom: 15 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#FFF', marginBottom: 15 },
  btnMain: { backgroundColor: '#4DA8DA', padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 5 },
  btnText: { color: '#000', fontWeight: 'bold' },
  sectionTitle: { color: '#666', fontSize: 11, fontWeight: 'bold', marginTop: 10, marginBottom: 10 },
  btnAddSmall: { backgroundColor: '#2C2C30', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6, borderWidth: 1, borderColor: '#444' },
  workoutCard: { backgroundColor: '#1A1A1D', borderRadius: 12, padding: 15, marginBottom: 10 },
  workoutDate: { color: '#888', fontSize: 12, fontWeight: 'bold', marginBottom: 5 },
  workoutName: { color: '#FFF', fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  workoutStat: { color: '#CCC', fontSize: 14, fontWeight: 'bold' },
  proposedBadge: { backgroundColor: '#F6B352', color: '#000', fontSize: 10, fontWeight: 'bold', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, overflow: 'hidden', marginLeft: 'auto' },
  insightText: { color: '#CCC', fontSize: 14, lineHeight: 20 },
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 }
});

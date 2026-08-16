import React, { useState, useEffect } from 'react';
import {
  StyleSheet, Text, View, TextInput, ScrollView, ActivityIndicator,
  Alert, TouchableOpacity, Modal, Dimensions
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';

import AvailabilityModal from './AvailabilityModal';
import DebugScreen from './DebugScreen';
import GoalDetailsModal from './GoalDetailsModal';
import AddGoalModal from './AddGoalModal';
import { ChatModal } from './ChatModal';
import { WorkoutChart } from './components/WorkoutChart';
import { AddWorkoutModal } from './components/AddWorkoutModal';
import { GenerateMicrocycleModal } from './components/GenerateMicrocycleModal';
import { AnalyticsScreen } from './screens/AnalyticsScreen';
import { PlanScreen } from './screens/PlanScreen';

import { LanguageProvider, useLanguage } from './i18n/LanguageContext';
import { API_URL } from './config';
import { api } from './services/api';
import { AthleteSnapshot, TrainingPlanData, TrainingGoal, PlannedWorkout } from './types';

export default function App() {
  return (
    <LanguageProvider>
      <MainApp />
    </LanguageProvider>
  );
}

function MainApp() {
  const { t, language, setLanguage } = useLanguage();
  const [userId] = useState(1);
  const [athleteId, setAthleteId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [fullData, setFullData] = useState<AthleteSnapshot | null>(null);
  const [atpData, setAtpData] = useState<any>(null);
  const [loadingAtp, setLoadingAtp] = useState(false);

  // Tab & View States
  const [activeTab, setActiveTab] = useState<'Analytics' | 'Plan'>('Analytics');
  const [planData, setPlanData] = useState<TrainingPlanData | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);

  // Modals
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const [showReadinessDebug, setShowReadinessDebug] = useState(false);
  const [selectedWorkout, setSelectedWorkout] = useState<PlannedWorkout | null>(null);
  const [selectedGoalDetails, setSelectedGoalDetails] = useState<TrainingGoal | null>(null);
  const [showChatModal, setShowChatModal] = useState(false);
  const [showAddWorkoutModal, setShowAddWorkoutModal] = useState(false);
  const [showGenerateMicrocycleModal, setShowGenerateMicrocycleModal] = useState(false);
  const [syncingIntervals, setSyncingIntervals] = useState(false);

  useEffect(() => {
    init();
  }, []);

  useEffect(() => {
    if (activeTab === 'Plan' && !loadingPlan) {
      fetchPlan();
    }
  }, [activeTab]);

  const init = async () => {
    const id = await AsyncStorage.getItem('athleteId');
    const key = await AsyncStorage.getItem('apiKey');
    if (id) setAthleteId(id);
    if (key) setApiKey(key);
    if (id && key) {
      syncAll(id, key);
    }
  };

  const syncAll = async (id = athleteId, key = apiKey, forceRefresh = false) => {
    if (!id || !key) return;
    setLoading(true);
    try {
      await api.setupKeys(userId, id, key);
      await AsyncStorage.setItem('athleteId', id);
      await AsyncStorage.setItem('apiKey', key);
      const snapshot = await api.getAnalysis(userId, forceRefresh);
      setFullData(snapshot);
      setShowSettings(false);
    } catch (e: any) {
      Alert.alert(t('error'), `${t('conn_error')} ${e.message || ''}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlan = async () => {
    setLoadingPlan(true);
    try {
      const plan = await api.getPlan(userId);
      setPlanData(plan);
      if (plan.annual_training_plan) {
        setAtpData(plan.annual_training_plan);
      }
    } catch (e: any) {
      console.log("Error fetching plan:", e);
    } finally {
      setLoadingPlan(false);
    }
  };

  const handleGenerateATP = async () => {
    setLoadingAtp(true);
    try {
      const res = await api.generateATP(userId);
      if (res.status === 'error') {
        Alert.alert(t('error'), res.data?.data || t('no_future_goals'));
      } else {
        setAtpData(res.data);
      }
    } catch (e) {
      Alert.alert(t('error'), t('gen_atp_error'));
    } finally {
      setLoadingAtp(false);
    }
  };

  const handleApprovePlan = async (planId: number) => {
    setLoadingPlan(true);
    try {
      await api.approveRevision(planId);
      Alert.alert(t('success'), t('plan_updated'));
      fetchPlan();
    } catch (e) {
      Alert.alert(t('error'), t('approve_fail'));
      setLoadingPlan(false);
    }
  };

  const handleRejectPlan = async (planId: number) => {
    setLoadingPlan(true);
    try {
      await api.rejectRevision(planId);
      Alert.alert(t('rejected'), t('returned_to_original'));
      fetchPlan();
    } catch (e) {
      Alert.alert(t('error'), t('reject_fail'));
      setLoadingPlan(false);
    }
  };

  const handleSyncIntervals = async () => {
    const mcId = planData?.microcycles?.[0]?.id;
    if (!mcId) {
      Alert.alert(t('error'), 'Brak mikrocyklu do synchronizacji. Wygeneruj mikrocykl najpierw.');
      return;
    }
    setSyncingIntervals(true);
    try {
      const res = await api.syncMicrocycleToIntervals(mcId);
      if (res.success) {
        Alert.alert(t('success'), `${t('sync_success')} (${res.synced_workouts} jednostek)`);
        fetchPlan();
      } else {
        Alert.alert(t('error'), res.error || 'Błąd synchronizacji.');
      }
    } catch (e: any) {
      Alert.alert(t('error'), 'Błąd połączenia z serwerem.');
    } finally {
      setSyncingIntervals(false);
    }
  };

  const handleDeleteWorkout = async (workoutId: number) => {
    Alert.alert(
      t('delete'),
      t('delete_workout_confirm'),
      [
        { text: t('cancel'), style: 'cancel' },
        {
          text: t('delete'),
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteWorkout(workoutId);
              setSelectedWorkout(null);
              fetchPlan();
            } catch (e) {
              Alert.alert(t('error'), 'Błąd usuwania treningu.');
            }
          }
        }
      ]
    );
  };

  const handleDeleteGoal = async (goalId: number) => {
    Alert.alert(
      t('delete_goal'),
      t('delete_confirm'),
      [
        { text: t('cancel'), style: 'cancel' },
        {
          text: t('delete'),
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteGoal(goalId);
              setSelectedGoalDetails(null);
              syncAll();
            } catch (e) {
              Alert.alert(t('error'), t('conn_error_goal'));
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.mainContainer}>
      {showDebug ? (
        <DebugScreen userId={userId} apiUrl={API_URL} onClose={() => setShowDebug(false)} />
      ) : (
        <>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.headerTitle}>{activeTab === 'Analytics' ? t('analytics') : t('training_plan')}</Text>
              <Text style={styles.headerSubtitle}>{fullData?.meta?.athlete_name || t('syncing')}</Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <TouchableOpacity
                onPress={() => setLanguage(language === 'en' ? 'pl' : 'en')}
                style={styles.langBtn}
              >
                <Text style={styles.langBtnText}>{language.toUpperCase()}</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setShowDebug(true)} style={{ marginRight: 15 }}>
                <Ionicons name="bug-outline" size={24} color="#F23661" />
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setShowSettings(!showSettings)}>
                <Ionicons name="settings-outline" size={24} color="#FFF" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Main Content */}
          {!fullData && !showSettings && athleteId && loading ? (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
              <ActivityIndicator size="large" color="#4DA8DA" />
            </View>
          ) : showSettings ? (
            <ScrollView contentContainerStyle={styles.scroll}>
              <View style={styles.card}>
                <Text style={styles.cardTitle}>{t('data_source')}</Text>
                <TextInput
                  placeholderTextColor="#666"
                  placeholder={t('intervals_id')}
                  value={athleteId}
                  onChangeText={setAthleteId}
                  style={styles.input}
                  keyboardType="numeric"
                />
                <TextInput
                  placeholderTextColor="#666"
                  placeholder={t('api_key')}
                  value={apiKey}
                  onChangeText={setApiKey}
                  style={styles.input}
                  secureTextEntry
                />
                <TouchableOpacity
                  style={[styles.btnMain, { backgroundColor: '#73E491', marginTop: 15 }]}
                  onPress={() => setShowAvailabilityModal(true)}
                >
                  <Text style={styles.btnText}>{t('edit_availability')}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btnMain, { marginTop: 15 }]}
                  onPress={() => syncAll()}
                >
                  <Text style={styles.btnText}>{t('connect_sync')}</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          ) : (
            <>
              {activeTab === 'Analytics' ? (
                <AnalyticsScreen
                  data={fullData}
                  loading={loading}
                  onRefresh={() => syncAll(athleteId, apiKey, true)}
                  onOpenReadinessDebug={() => setShowReadinessDebug(true)}
                />
              ) : (
                <PlanScreen
                  planData={planData}
                  loadingPlan={loadingPlan}
                  onRefreshPlan={fetchPlan}
                  goals={fullData?.user_goals || []}
                  atpData={atpData}
                  loadingAtp={loadingAtp}
                  onGenerateATP={handleGenerateATP}
                  onResetAtpData={() => setAtpData(null)}
                  onApprovePlan={handleApprovePlan}
                  onRejectPlan={handleRejectPlan}
                  onSelectWorkout={setSelectedWorkout}
                  onSelectGoalDetails={setSelectedGoalDetails}
                  onOpenAddGoal={() => setShowGoalForm(true)}
                  onOpenAddWorkout={() => setShowAddWorkoutModal(true)}
                  onOpenGenerateMicrocycle={() => setShowGenerateMicrocycleModal(true)}
                  onSyncIntervals={handleSyncIntervals}
                  syncingIntervals={syncingIntervals}
                />
              )}

              {/* Bottom Tab Bar */}
              <View style={styles.tabBar}>
                <TouchableOpacity style={styles.tabBtn} onPress={() => setActiveTab('Analytics')}>
                  <Ionicons name={activeTab === 'Analytics' ? "pie-chart" : "pie-chart-outline"} size={24} color={activeTab === 'Analytics' ? "#4DA8DA" : "#888"} />
                  <Text style={[styles.tabText, { color: activeTab === 'Analytics' ? "#4DA8DA" : "#888" }]}>{t('analytics')}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.tabBtn} onPress={() => setActiveTab('Plan')}>
                  <MaterialCommunityIcons name={activeTab === 'Plan' ? "calendar-month" : "calendar-month-outline"} size={26} color={activeTab === 'Plan' ? "#4DA8DA" : "#888"} />
                  <Text style={[styles.tabText, { color: activeTab === 'Plan' ? "#4DA8DA" : "#888" }]}>{t('training_plan')}</Text>
                </TouchableOpacity>
              </View>
            </>
          )}

          {/* Modale */}
          <AvailabilityModal
            visible={showAvailabilityModal}
            onClose={() => setShowAvailabilityModal(false)}
            userId={userId}
            apiUrl={API_URL}
          />

          <GoalDetailsModal
            isVisible={!!selectedGoalDetails}
            onClose={() => setSelectedGoalDetails(null)}
            goal={selectedGoalDetails}
            apiUrl={API_URL}
            onGoalUpdated={() => {
              setSelectedGoalDetails(null);
              syncAll();
            }}
            onDelete={handleDeleteGoal}
          />

          <AddGoalModal
            isVisible={showGoalForm}
            onClose={() => {
              setShowGoalForm(false);
              syncAll();
            }}
            userId={userId}
          />

          <AddWorkoutModal
            visible={showAddWorkoutModal}
            onClose={() => setShowAddWorkoutModal(false)}
            onWorkoutAdded={() => {
              fetchPlan();
              syncAll();
            }}
            microcycleId={planData?.microcycles?.[0]?.id}
            planId={planData?.plan?.id}
            apiUrl={API_URL}
          />

          <GenerateMicrocycleModal
            visible={showGenerateMicrocycleModal}
            onClose={() => setShowGenerateMicrocycleModal(false)}
            onGenerated={() => {
              fetchPlan();
              syncAll();
            }}
            userId={userId}
            goals={fullData?.user_goals || []}
            apiUrl={API_URL}
          />

          {/* Readiness Debugger Modal */}
          <Modal visible={showReadinessDebug} animationType="slide" transparent>
            <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'center', padding: 20 }}>
              <View style={{ backgroundColor: '#1A1A1D', padding: 20, borderRadius: 12, borderWidth: 1, borderColor: '#333' }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15 }}>
                  <Text style={{ color: '#FFF', fontSize: 18, fontWeight: 'bold' }}>{t('readiness_debugger')}</Text>
                  <TouchableOpacity onPress={() => setShowReadinessDebug(false)}>
                    <MaterialCommunityIcons name="close" size={24} color="#FFF" />
                  </TouchableOpacity>
                </View>
                <ScrollView style={{ maxHeight: Dimensions.get('window').height * 0.6 }}>
                  <Text style={{ color: '#F6B352', fontWeight: 'bold', marginTop: 10 }}>{t('training_readiness')}</Text>
                  <Text style={{ color: '#CCC', fontSize: 12 }}>{JSON.stringify(fullData?.pmc?.readiness_details, null, 2)}</Text>
                  <Text style={{ color: '#B66DFF', fontWeight: 'bold', marginTop: 20 }}>{t('hrv_status_debug')}</Text>
                  <Text style={{ color: '#CCC', fontSize: 12 }}>{JSON.stringify(fullData?.pmc?.hrv_details, null, 2)}</Text>
                </ScrollView>
              </View>
            </View>
          </Modal>

          {/* Workout Details Modal */}
          <Modal visible={!!selectedWorkout} animationType="slide" transparent>
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>{selectedWorkout?.name || t('details')}</Text>
                  <TouchableOpacity onPress={() => setSelectedWorkout(null)} style={styles.closeBtn}>
                    <MaterialCommunityIcons name="close" size={24} color="#FFF" />
                  </TouchableOpacity>
                </View>

                <View style={styles.modalStatsRow}>
                  <View style={styles.modalStatItem}>
                    <Text style={styles.modalStatLabel}>{t('time')}</Text>
                    <Text style={styles.modalStatValue}>{selectedWorkout?.planned_duration_minutes}m</Text>
                  </View>
                  <View style={styles.modalStatItem}>
                    <Text style={styles.modalStatLabel}>TSS</Text>
                    <Text style={{ ...styles.modalStatValue, color: '#73E491' }}>{selectedWorkout?.planned_tss}</Text>
                  </View>
                  <View style={styles.modalStatItem}>
                    <Text style={styles.modalStatLabel}>{t('sport')}</Text>
                    <Text style={styles.modalStatValue}>{selectedWorkout?.workout_type}</Text>
                  </View>
                </View>

                <WorkoutChart workoutDoc={selectedWorkout?.workout_doc || selectedWorkout?.structure} />

                <View style={{ ...styles.divider, marginBottom: 15 }} />

                <Text style={styles.modalSectionLabel}>{t('workout_desc')}</Text>
                <ScrollView style={styles.modalDescScroll}>
                  <Text style={styles.modalDescText}>
                    {selectedWorkout?.description || t('no_description')}
                  </Text>
                </ScrollView>

                {selectedWorkout?.source === 'local' && (
                  <TouchableOpacity
                    style={styles.btnDeleteWorkout}
                    onPress={() => handleDeleteWorkout(Number(selectedWorkout.id))}
                  >
                    <Text style={{ color: '#F23661', fontWeight: 'bold' }}>🗑️ {t('delete')}</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          </Modal>

          {/* AI Coach Floating Button */}
          <TouchableOpacity
            style={styles.floatingChatBtn}
            onPress={() => setShowChatModal(true)}
          >
            <Text style={{ fontSize: 18, marginRight: 6 }}>💬</Text>
            <Text style={{ color: '#FFF', fontWeight: 'bold', fontSize: 14 }}>Trener AI</Text>
          </TouchableOpacity>

          <ChatModal
            visible={showChatModal}
            onClose={() => setShowChatModal(false)}
            userId={userId}
            apiBaseUrl={API_URL}
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  mainContainer: { flex: 1, backgroundColor: '#0B0B0C' },
  header: { paddingTop: 60, paddingBottom: 20, backgroundColor: '#1A1A1D', paddingHorizontal: 20, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  headerSubtitle: { color: '#888', fontSize: 14 },
  langBtn: { marginRight: 15, backgroundColor: '#2C2C30', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6, borderWidth: 1, borderColor: '#444' },
  langBtnText: { color: '#FFF', fontSize: 12, fontWeight: 'bold' },
  scroll: { paddingBottom: 100, padding: 15 },
  card: { backgroundColor: '#1A1A1D', borderRadius: 12, padding: 20, marginBottom: 15 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#FFF', marginBottom: 15 },
  input: { backgroundColor: '#2C2C30', borderRadius: 8, padding: 12, marginBottom: 12, color: '#FFF' },
  btnMain: { backgroundColor: '#4DA8DA', padding: 15, borderRadius: 8, alignItems: 'center', marginTop: 5 },
  btnText: { color: '#000', fontWeight: 'bold' },
  tabBar: { flexDirection: 'row', backgroundColor: '#1A1A1D', paddingBottom: 30, paddingTop: 15, borderTopWidth: 1, borderTopColor: '#2C2C30', position: 'absolute', bottom: 0, width: '100%', justifyContent: 'space-around' },
  tabBtn: { alignItems: 'center' },
  tabText: { fontSize: 10, marginTop: 4, fontWeight: 'bold' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#1A1A1D', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 25, maxHeight: Dimensions.get('window').height * 0.85 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  modalTitle: { color: '#FFF', fontSize: 20, fontWeight: 'bold', flex: 1, marginRight: 15 },
  closeBtn: { padding: 5, backgroundColor: '#2C2C30', borderRadius: 20 },
  modalStatsRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  modalStatItem: { alignItems: 'center', flex: 1 },
  modalStatLabel: { color: '#888', fontSize: 10, fontWeight: 'bold', letterSpacing: 1, marginBottom: 5 },
  modalStatValue: { color: '#FFF', fontSize: 22, fontWeight: 'bold' },
  divider: { height: 1, backgroundColor: '#2C2C30', width: '100%' },
  modalSectionLabel: { color: '#888', fontSize: 12, fontWeight: 'bold', letterSpacing: 1, marginBottom: 10 },
  modalDescScroll: { maxHeight: 300 },
  modalDescText: { color: '#CCC', fontSize: 14, lineHeight: 22 },
  btnDeleteWorkout: { backgroundColor: '#2C2C30', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 15, borderWidth: 1, borderColor: '#F23661' },
  floatingChatBtn: { position: 'absolute', bottom: 80, right: 20, backgroundColor: '#3B82F6', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 25, flexDirection: 'row', alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 5, elevation: 6, zIndex: 999 }
});
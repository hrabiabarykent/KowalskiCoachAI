import axios from 'axios';
import { API_URL } from '../config';
import {
  AthleteSnapshot,
  TrainingPlanData,
  Dictionaries,
  TrainingGoal,
  MicrocycleSummary,
  PlannedWorkout
} from '../types';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const api = {
  // Setup & Sync
  setupKeys: async (userId: number, intervalsId: string, intervalsApiKey: string) => {
    const res = await apiClient.post('/setup-keys', {
      user_id: userId,
      intervals_id: intervalsId,
      intervals_api_key: intervalsApiKey
    });
    return res.data;
  },

  // Analysis & Athlete Snapshot
  getAnalysis: async (userId: number, forceRefresh: boolean = false): Promise<AthleteSnapshot> => {
    const res = await apiClient.post('/analyze', {
      user_id: userId,
      force_refresh: forceRefresh
    });
    return res.data.data;
  },

  getDictionaries: async (): Promise<Dictionaries> => {
    const res = await apiClient.get('/dictionaries');
    return res.data;
  },

  // Goals
  createGoal: async (goalData: Partial<TrainingGoal> & { user_id: number }) => {
    const res = await apiClient.post('/goals', goalData);
    return res.data;
  },

  deleteGoal: async (goalId: number) => {
    const res = await apiClient.delete(`/goals/${goalId}`);
    return res.data;
  },

  evaluateGoal: async (goalId: number) => {
    const res = await apiClient.post(`/evaluate-goal/${goalId}`);
    return res.data;
  },

  // ATP
  generateATP: async (userId: number) => {
    const res = await apiClient.post('/atp', { user_id: userId });
    return res.data;
  },

  // Training Plan & Revisions
  getPlan: async (userId: number): Promise<TrainingPlanData> => {
    const res = await apiClient.get(`/plan/${userId}`);
    return res.data;
  },

  approveRevision: async (planId: number) => {
    const res = await apiClient.post(`/revision/approve/${planId}`);
    return res.data;
  },

  rejectRevision: async (planId: number) => {
    const res = await apiClient.post(`/revision/reject/${planId}`);
    return res.data;
  },

  // Microcycles
  generateMicrocycle: async (data: {
    user_id: number;
    plan_id?: number;
    week_number?: number;
    start_date?: string;
    target_tss?: number;
    goal_id?: number | null;
    focus?: string;
  }) => {
    const res = await apiClient.post('/plan/microcycle/generate', data);
    return res.data;
  },

  getMicrocycle: async (microcycleId: number): Promise<MicrocycleSummary> => {
    const res = await apiClient.get(`/plan/microcycle/${microcycleId}`);
    return res.data;
  },

  syncMicrocycleToIntervals: async (microcycleId: number) => {
    const res = await apiClient.post(`/plan/microcycle/${microcycleId}/sync-intervals`);
    return res.data;
  },

  // Workouts CRUD
  createWorkout: async (workoutData: Partial<PlannedWorkout>) => {
    const res = await apiClient.post('/plan/workout', workoutData);
    return res.data;
  },

  updateWorkout: async (workoutId: number, updateData: Partial<PlannedWorkout>) => {
    const res = await apiClient.put(`/plan/workout/${workoutId}`, updateData);
    return res.data;
  },

  deleteWorkout: async (workoutId: number) => {
    const res = await apiClient.delete(`/plan/workout/${workoutId}`);
    return res.data;
  }
};

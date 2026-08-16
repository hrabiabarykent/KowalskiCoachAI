export type SportDiscipline = 'Bike' | 'Run' | 'Swim' | 'Triathlon' | 'Strength' | 'Rest' | string;
export type GoalPriority = 'A' | 'B' | 'C';
export type IntensityCategory = 'RECOVERY' | 'AEROBIC_BASE' | 'TEMPO' | 'THRESHOLD' | 'VO2MAX' | 'REST' | string;

export interface TrainingGoal {
  id: number;
  user_id: number;
  priority: GoalPriority;
  discipline: SportDiscipline;
  event_name: string;
  event_type?: string;
  event_date: string;
  target_time_str?: string;
  is_recreational?: boolean;
  ai_evaluation?: string;
  weeks_until?: number;
}

export interface PlannedWorkout {
  id: string | number;
  plan_id?: number;
  microcycle_id?: number;
  date: string;
  name: string;
  workout_type: SportDiscipline;
  intensity_category?: IntensityCategory;
  is_key_workout?: boolean;
  description?: string;
  workout_doc?: any;
  structure?: any;
  planned_duration_minutes: number;
  planned_tss: number;
  status: 'Pending' | 'Completed' | 'Missed' | 'Skipped' | 'Proposed' | 'APPROVED' | string;
  source?: 'local' | 'intervals' | string;
  color?: string;
  intervals_event_id?: string;
}

export interface MicrocycleSummary {
  id: number;
  plan_id: number;
  goal_id?: number;
  goal_name?: string;
  week_number: number;
  start_date: string;
  end_date: string;
  phase: string;
  focus?: string;
  target_tss: number;
  target_hours: number;
  total_planned_tss: number;
  total_planned_minutes: number;
  status: string;
  notes?: string;
  workouts?: PlannedWorkout[];
}

export interface TrainingPlanData {
  has_plan: boolean;
  plan?: {
    id: number;
    status: string;
    current_phase: string;
  } | null;
  workouts: PlannedWorkout[];
  microcycles?: MicrocycleSummary[];
  annual_training_plan?: any;
}

export interface AthleteSnapshot {
  meta?: {
    athlete_name?: string;
    weight?: number;
    ftp?: number;
  };
  metrics?: {
    fitness_ctl?: number;
    fatigue_atl?: number;
    form_tsb?: number;
    vdot?: number;
    eftp?: number;
    readiness_score?: number;
  };
  fitness_trends?: Array<{
    date: string;
    ctl: number;
    atl: number;
    tsb: number;
    resting_hr?: number;
  }>;
  weekly_hrv?: Array<{
    date: string;
    avg_hrv: number;
  }>;
  user_goals?: TrainingGoal[];
  pmc?: {
    readiness_details?: any;
    hrv_details?: any;
  };
  coach_insights?: string;
}

export interface Dictionaries {
  [sport: string]: string[];
}

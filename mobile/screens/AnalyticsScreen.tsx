import React from 'react';
import {
  ScrollView, View, Text, StyleSheet, RefreshControl, Dimensions, TouchableOpacity
} from 'react-native';
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { useLanguage } from '../i18n/LanguageContext';
import { AthleteSnapshot } from '../types';

const screenWidth = Dimensions.get("window").width;

interface AnalyticsScreenProps {
  data: AthleteSnapshot | null;
  loading: boolean;
  onRefresh: () => void;
  onOpenReadinessDebug: () => void;
}

export const AnalyticsScreen: React.FC<AnalyticsScreenProps> = ({
  data,
  loading,
  onRefresh,
  onOpenReadinessDebug
}) => {
  const { t } = useLanguage();

  const fitnessData = {
    labels: data?.fitness_trends ? data.fitness_trends.map((item, i) => i % 14 === 0 ? item.date.slice(5) : '').filter(Boolean) : [],
    datasets: [
      { data: data?.fitness_trends?.map(item => item.ctl) || [0], color: () => '#4DA8DA', strokeWidth: 2 },
      { data: data?.fitness_trends?.map(item => item.atl) || [0], color: () => '#F6B352', strokeWidth: 2 }
    ],
    legend: ["CTL (Fitness)", "ATL (Fatigue)"]
  };

  const rhrData = {
    labels: data?.fitness_trends?.slice(-30).map((item, i) => i % 5 === 0 ? item.date.slice(5) : '').filter(Boolean) || [],
    datasets: [{ data: data?.fitness_trends?.slice(-30).map(item => item.resting_hr || 0) || [0] }]
  };

  const chartConfig = {
    backgroundGradientFrom: '#1A1A1D',
    backgroundGradientTo: '#1A1A1D',
    color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(150, 150, 150, ${opacity})`,
    strokeWidth: 2,
    useShadowColorFromDataset: false,
    propsForDots: { r: "0" }
  };

  return (
    <ScrollView
      contentContainerStyle={styles.scroll}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={onRefresh} tintColor="#FFF" />}
    >
      {/* KPI Row 1 */}
      <View style={styles.kpiRow}>
        <View style={styles.kpiBox}>
          <Text style={styles.kpiLabel}>{t('eftp')}</Text>
          <Text style={styles.kpiVal}>{data?.metrics?.eftp ? Math.round(data.metrics.eftp) : (data?.meta?.ftp || '--')} <Text style={styles.kpiUnit}>W</Text></Text>
        </View>
        <View style={styles.kpiBox}>
          <Text style={styles.kpiLabel}>{t('vdot')}</Text>
          <Text style={styles.kpiVal}>{data?.metrics?.vdot || '--'}</Text>
        </View>
        <View style={styles.kpiBox}>
          <Text style={styles.kpiLabel}>{t('fitness')}</Text>
          <Text style={{ ...styles.kpiVal, color: '#4DA8DA' }}>{data?.metrics?.fitness_ctl ? Math.round(data.metrics.fitness_ctl) : '--'} <Text style={styles.kpiUnit}>CTL</Text></Text>
        </View>
      </View>

      {/* KPI Row 2 */}
      <View style={styles.kpiRow}>
        <TouchableOpacity style={styles.kpiBox} onPress={onOpenReadinessDebug}>
          <Text style={styles.kpiLabel}>{t('readiness_score')}</Text>
          <Text style={{ ...styles.kpiVal, color: (data?.metrics?.readiness_score || 0) > 70 ? '#73E491' : '#F6B352' }}>
            {data?.metrics?.readiness_score || '--'}<Text style={styles.kpiUnit}>/100</Text>
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.kpiBox} onPress={onOpenReadinessDebug}>
          <Text style={styles.kpiLabel}>{t('hrv_avg')}</Text>
          <Text style={styles.kpiVal}>{data?.weekly_hrv?.slice(-1)[0]?.avg_hrv ? Math.round(data.weekly_hrv.slice(-1)[0].avg_hrv) : '--'} <Text style={styles.kpiUnit}>ms</Text></Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.kpiBox} onPress={onOpenReadinessDebug}>
          <Text style={styles.kpiLabel}>{t('hrv_status')}</Text>
          <Text style={{ ...styles.kpiVal, fontSize: 13, color: '#73E491' }}>
            {data?.pmc?.hrv_details?.status || 'BALANCED'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Coach Insights */}
      {data?.coach_insights && (
        <View style={styles.insightCard}>
          <View style={styles.row}>
            <MaterialCommunityIcons name="lightbulb-on" size={18} color="#F6B352" />
            <Text style={styles.insightTitle}>{t('coach_insights')}</Text>
          </View>
          <Text style={styles.insightText}>{data.coach_insights}</Text>
        </View>
      )}

      {/* Fitness Trends Chart */}
      <View style={styles.chartCard}>
        <Text style={styles.chartTitle}>{t('fitness_trends')} <Text style={styles.kpiUnit}>(CTL / ATL)</Text></Text>
        {fitnessData.datasets[0].data.length > 1 ? (
          <LineChart
            data={fitnessData}
            width={screenWidth - 30}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={{ borderRadius: 12 }}
            withInnerLines={false}
          />
        ) : (
          <Text style={{ color: '#666', padding: 20, textAlign: 'center' }}>{t('no_data')}</Text>
        )}
      </View>

      {/* Resting Heart Rate Chart */}
      <View style={styles.chartCard}>
        <Text style={styles.chartTitle}>{t('resting_hr')} <Text style={styles.kpiUnit}>{t('last_30_days')}</Text></Text>
        {rhrData.datasets[0].data.length > 1 ? (
          <BarChart
            data={rhrData}
            width={screenWidth - 30}
            height={200}
            yAxisLabel=""
            yAxisSuffix=""
            chartConfig={{ ...chartConfig, color: (opacity = 1) => `rgba(242, 115, 112, ${opacity})` }}
            style={{ borderRadius: 12 }}
            withInnerLines={false}
          />
        ) : (
          <Text style={{ color: '#666', padding: 20, textAlign: 'center' }}>{t('no_data')}</Text>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scroll: { paddingBottom: 100, padding: 15 },
  kpiRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  kpiBox: { backgroundColor: '#1A1A1D', borderRadius: 12, padding: 14, width: (screenWidth - 46) / 3 },
  kpiLabel: { color: '#888', fontSize: 10, fontWeight: 'bold', marginBottom: 6 },
  kpiVal: { color: '#FFF', fontSize: 20, fontWeight: 'bold' },
  kpiUnit: { color: '#888', fontSize: 11, fontWeight: 'normal' },
  insightCard: { backgroundColor: '#1A1A1D', borderRadius: 12, padding: 15, marginBottom: 16, borderLeftWidth: 3, borderLeftColor: '#F6B352' },
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  insightTitle: { color: '#FFF', fontSize: 12, fontWeight: 'bold', marginLeft: 8 },
  insightText: { color: '#CCC', fontSize: 13, lineHeight: 19 },
  chartCard: { backgroundColor: '#1A1A1D', borderRadius: 12, paddingVertical: 15, marginBottom: 16, overflow: 'hidden' },
  chartTitle: { color: '#888', fontSize: 11, fontWeight: 'bold', marginLeft: 15, marginBottom: 10 }
});

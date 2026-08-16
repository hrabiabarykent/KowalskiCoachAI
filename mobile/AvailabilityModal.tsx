import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, Switch, ActivityIndicator, Alert } from 'react-native';
import Slider from '@react-native-community/slider';
import axios from 'axios';
import { useLanguage } from './i18n/LanguageContext';

const getDays = (t: any) => [
    { key: 'Monday', label: t('monday') },
    { key: 'Tuesday', label: t('tuesday') },
    { key: 'Wednesday', label: t('wednesday') },
    { key: 'Thursday', label: t('thursday') },
    { key: 'Friday', label: t('friday') },
    { key: 'Saturday', label: t('saturday') },
    { key: 'Sunday', label: t('sunday') }
];

const getSports = (t: any) => [t('cycling'), t('running'), t('swimming')];

interface AvailabilityProps {
    visible: boolean;
    onClose: () => void;
    userId: number;
    apiUrl: string;
}

export default function AvailabilityModal({ visible, onClose, userId, apiUrl }: AvailabilityProps) {
    const { t } = useLanguage();
    const DAYS = getDays(t);
    const SPORTS = getSports(t);
    const [loading, setLoading] = useState(false);
    const [schedule, setSchedule] = useState<{ [key: string]: { enabled: boolean, max_hours: number, sports: string[] } }>({});

    useEffect(() => {
        if (visible) {
            fetchAvailability();
        }
    }, [visible]);

    const fetchAvailability = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${apiUrl}/user/${userId}/availability`);
            const data = res.data;

            // Initialize defaults if missing
            const merged: any = {};
            DAYS.forEach(d => {
                if (data[d.key]) merged[d.key] = data[d.key];
                else merged[d.key] = { enabled: false, max_hours: 2, sports: [] };
            });
            setSchedule(merged);
        } catch (e) {
            console.log("Error loading availability", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            await axios.post(`${apiUrl}/user/${userId}/availability`, { user_id: userId, availability: schedule });
            Alert.alert(t('success'), t('availability_saved'));
            onClose();
        } catch (e) {
            Alert.alert(t('error'), t('could_not_save_availability'));
        } finally {
            setLoading(false);
        }
    };

    const toggleDay = (dayKey: string, val: boolean) => {
        setSchedule(prev => ({ ...prev, [dayKey]: { ...prev[dayKey], enabled: val } }));
    };

    const changeHours = (dayKey: string, val: number) => {
        setSchedule(prev => ({ ...prev, [dayKey]: { ...prev[dayKey], max_hours: val } }));
    };

    const toggleSport = (dayKey: string, sport: string) => {
        setSchedule(prev => {
            const arr = prev[dayKey].sports;
            // append or remove
            let newSports = arr.includes(sport) ? arr.filter(s => s !== sport) : [...arr, sport];
            return { ...prev, [dayKey]: { ...prev[dayKey], sports: newSports } };
        });
    };

    // Calculate total hours
    const totalWeeklyHours = Object.values(schedule).reduce((acc, curr) => acc + (curr.enabled ? curr.max_hours : 0), 0);

    return (
        <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
            <View style={styles.container}>
                <View style={styles.header}>
                    <Text style={styles.title}>{t('available_days')}</Text>
                    <TouchableOpacity onPress={onClose}><Text style={styles.closeBtn}>{t('done')}</Text></TouchableOpacity>
                </View>

                {loading ? (
                    <ActivityIndicator style={{ marginTop: 50 }} color="#73E491" />
                ) : (
                    <ScrollView contentContainerStyle={{ padding: 15, paddingBottom: 100 }}>
                        {DAYS.map(day => {
                            const data = schedule[day.key] || { enabled: false, max_hours: 0, sports: [] };
                            return (
                                <View key={day.key} style={[styles.dayCard, data.enabled && styles.dayCardActive]}>
                                    <View style={styles.dayHeader}>
                                        <View style={styles.row}>
                                            <Switch value={data.enabled} onValueChange={(v) => toggleDay(day.key, v)} trackColor={{ false: '#3A3A3D', true: '#5CB85C' }} thumbColor="#FFF" />
                                            <Text style={styles.dayLabel}>{day.label}</Text>
                                        </View>
                                        <Text style={styles.hoursLabel}>{data.max_hours}h</Text>
                                    </View>

                                    {data.enabled && (
                                        <View style={styles.controls}>
                                            <Slider
                                                style={{ width: '100%', height: 40 }}
                                                minimumValue={0}
                                                maximumValue={10}
                                                step={0.5}
                                                value={data.max_hours}
                                                onValueChange={(v) => changeHours(day.key, v)}
                                                minimumTrackTintColor="#73E491"
                                                maximumTrackTintColor="#333"
                                                thumbTintColor="#FFF"
                                            />
                                            <View style={styles.sliderLabels}>
                                                <Text style={styles.smText}>30m</Text>
                                                <Text style={styles.smText}>2h</Text>
                                                <Text style={styles.smText}>5h</Text>
                                                <Text style={styles.smText}>10h</Text>
                                            </View>

                                            <View style={styles.sportsRow}>
                                                <Text style={styles.smText}>{t('sports')}: </Text>
                                                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                                                    {SPORTS.map(s => {
                                                        const isActive = data.sports.includes(s);
                                                        return (
                                                            <TouchableOpacity key={s} onPress={() => toggleSport(day.key, s)} style={[styles.pill, isActive && styles.pillActive]}>
                                                                <Text style={[styles.pillText, isActive && styles.pillTextActive]}>{s}</Text>
                                                            </TouchableOpacity>
                                                        )
                                                    })}
                                                </ScrollView>
                                            </View>
                                        </View>
                                    )}
                                </View>
                            )
                        })}
                    </ScrollView>
                )}

                <View style={styles.footer}>
                    <TouchableOpacity style={styles.saveBtn} onPress={handleSave}>
                        <Text style={styles.saveBtnText}>{t('save_schedule')}</Text>
                    </TouchableOpacity>
                    <Text style={styles.totalText}>{t('target_weekly_time')}: <Text style={{ color: '#FFF' }}>{totalWeeklyHours}h</Text></Text>
                </View>

            </View>
        </Modal>
    )
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#000' },
    header: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, paddingTop: 40, backgroundColor: '#0B0B0C' },
    title: { color: '#FFF', fontSize: 20, fontWeight: 'bold' },
    closeBtn: { color: '#73E491', fontSize: 16, marginTop: 4 },
    dayCard: { backgroundColor: '#111', borderRadius: 12, padding: 15, marginBottom: 12, borderWidth: 1, borderColor: '#333' },
    dayCardActive: { borderColor: '#73E491' },
    dayHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    row: { flexDirection: 'row', alignItems: 'center' },
    dayLabel: { color: '#FFF', fontSize: 16, fontWeight: 'bold', marginLeft: 10 },
    hoursLabel: { color: '#73E491', fontSize: 14, fontWeight: 'bold' },
    controls: { marginTop: 15 },
    sliderLabels: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 5, marginBottom: 15 },
    smText: { color: '#666', fontSize: 11 },
    sportsRow: { flexDirection: 'row', alignItems: 'center', marginTop: 10 },
    pill: { backgroundColor: '#222', borderRadius: 16, paddingVertical: 6, paddingHorizontal: 12, marginRight: 8, borderWidth: 1, borderColor: '#444' },
    pillActive: { backgroundColor: '#73E491', borderColor: '#73E491' },
    pillText: { color: '#888', fontSize: 12, fontWeight: 'bold' },
    pillTextActive: { color: '#000' },
    footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#0B0B0C', borderTopWidth: 1, borderTopColor: '#222' },
    totalText: { color: '#888', textAlign: 'center', marginTop: 15 },
    saveBtn: { backgroundColor: '#73E491', padding: 15, borderRadius: 8, alignItems: 'center' },
    saveBtnText: { color: '#000', fontWeight: 'bold', fontSize: 16 }
});

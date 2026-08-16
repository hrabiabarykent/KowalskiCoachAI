import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from './i18n/LanguageContext';

interface DebugScreenProps {
    userId: number;
    apiUrl: string;
    onClose: () => void;
}

export default function DebugScreen({ userId, apiUrl, onClose }: DebugScreenProps) {
    const { t } = useLanguage();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchDebugData();
    }, []);

    const fetchDebugData = async () => {
        try {
            setLoading(true);
            const res = await axios.get(`${apiUrl}/debug/${userId}`);
            setData(res.data);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch debug data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <View style={styles.container}>
                <View style={styles.header}>
                    <Text style={styles.headerTitle}>Debug Data</Text>
                    <TouchableOpacity onPress={onClose}>
                        <Ionicons name="close" size={28} color="#FFF" />
                    </TouchableOpacity>
                </View>
                <ActivityIndicator size="large" color="#4DA8DA" style={{ marginTop: 100 }} />
            </View>
        );
    }

    if (error) {
        return (
            <View style={styles.container}>
                <View style={styles.header}>
                    <Text style={styles.headerTitle}>Debug Data</Text>
                    <TouchableOpacity onPress={onClose}>
                        <Ionicons name="close" size={28} color="#FFF" />
                    </TouchableOpacity>
                </View>
                <Text style={styles.errorText}>Error: {error}</Text>
                <TouchableOpacity style={styles.btnMain} onPress={fetchDebugData}>
                    <Text style={styles.btnText}>{t('retry')}</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>{t('debug_data_dump')}</Text>
                <TouchableOpacity onPress={onClose}>
                    <Ionicons name="close" size={28} color="#FFF" />
                </TouchableOpacity>
            </View>
            <ScrollView contentContainerStyle={styles.scroll}>
                <View style={styles.codeBlock}>
                    <Text style={styles.codeText}>{JSON.stringify(data, null, 2)}</Text>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0B0B0C',
    },
    header: {
        paddingTop: 60,
        paddingBottom: 20,
        backgroundColor: '#1A1A1D',
        paddingHorizontal: 20,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    headerTitle: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
    },
    scroll: {
        padding: 15,
        paddingBottom: 50,
    },
    codeBlock: {
        backgroundColor: '#1E1E1E',
        padding: 15,
        borderRadius: 8,
    },
    codeText: {
        color: '#D4D4D4',
        fontFamily: 'monospace',
        fontSize: 12,
    },
    errorText: {
        color: '#F23661',
        textAlign: 'center',
        marginTop: 50,
        fontSize: 16,
    },
    btnMain: {
        backgroundColor: '#4DA8DA',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        margin: 20,
    },
    btnText: {
        color: '#000',
        fontWeight: 'bold',
    },
});

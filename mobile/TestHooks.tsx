import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';

export default function App() {
    const [test1] = useState(1);
    const [test2] = useState(2);
    useEffect(() => { console.log("Hooks initialized"); }, []);
    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#000' }}>
            <Text style={{ color: '#FFF' }}>Hooks work: {test1} {test2}</Text>
        </View>
    );
}

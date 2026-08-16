import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform
} from 'react-native';

interface ChatMessageDTO {
  id: number;
  user_id: number;
  sender: 'USER' | 'COACH';
  message: string;
  timestamp: string;
  suggested_action?: string;
}

interface ChatModalProps {
  visible: boolean;
  onClose: () => void;
  userId?: number;
  apiBaseUrl?: string;
}

export const ChatModal: React.FC<ChatModalProps> = ({
  visible,
  onClose,
  userId = 1,
  apiBaseUrl = 'http://localhost:8000'
}) => {
  const [messages, setMessages] = useState<ChatMessageDTO[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (visible) {
      fetchHistory();
    }
  }, [visible]);

  const fetchHistory = async () => {
    setFetchingHistory(true);
    try {
      const res = await fetch(`${apiBaseUrl}/chat/history/${userId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success') {
          setMessages(data.messages || []);
        }
      }
    } catch (e) {
      console.warn('Błąd pobierania historii czatu:', e);
    } finally {
      setFetchingHistory(false);
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 200);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    if (!textToSend) setInput('');
    setLoading(true);

    const coachMsgId = Date.now() + 1;
    const tempUserMsg: ChatMessageDTO = {
      id: Date.now(),
      user_id: userId,
      sender: 'USER',
      message: text,
      timestamp: new Date().toISOString()
    };

    const tempCoachMsg: ChatMessageDTO = {
      id: coachMsgId,
      user_id: userId,
      sender: 'COACH',
      message: '',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, tempUserMsg, tempCoachMsg]);
    setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);

    try {
      const res = await fetch(`${apiBaseUrl}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: text })
      });

      if (res.ok && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;

        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunkValue = decoder.decode(value, { stream: true });
            setMessages(prev =>
              prev.map(m =>
                m.id === coachMsgId ? { ...m, message: m.message + chunkValue } : m
              )
            );
            scrollViewRef.current?.scrollToEnd({ animated: false });
          }
        }
      } else {
        // Fallback do zwykłego API
        const fallbackRes = await fetch(`${apiBaseUrl}/chat/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, message: text })
        });
        if (fallbackRes.ok) {
          const data = await fallbackRes.json();
          if (data.coach_response) {
            setMessages(prev =>
              prev.map(m => (m.id === coachMsgId ? data.coach_response : m))
            );
          }
        }
      }
    } catch (e) {
      console.error('Błąd strumieniowania wiadomości:', e);
    } finally {
      setLoading(false);
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 200);
    }
  };


  const quickPrompts = [
    '💡 Wyjaśnij dzisiejszy trening',
    '🩹 Boli mnie łydka, co robić?',
    '🏃 Jak zastąpić rower biegiem?'
  ];

  return (
    <Modal visible={visible} animationType="slide" transparent={false} onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTitleRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>🤖</Text>
            </View>
            <View>
              <Text style={styles.headerTitle}>Trener Kowalski AI</Text>

              <Text style={styles.headerSubtitle}>Twój osobisty opiekun fizjologiczny</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Conversation View */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
        >
          {fetchingHistory ? (
            <ActivityIndicator size="small" color="#4A90E2" style={{ marginTop: 20 }} />
          ) : messages.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>💬</Text>
              <Text style={styles.emptyTitle}>Rozpocznij rozmowę z Trenerem</Text>

              <Text style={styles.emptyText}>
                Zadaj pytanie dotyczące dzisiejszego planu, formy, regeneracji lub ewentualnych kontuzji.
              </Text>
            </View>
          ) : (
            messages.map(item => {
              const isUser = item.sender === 'USER';
              return (
                <View
                  key={item.id}
                  style={[
                    styles.messageBubble,
                    isUser ? styles.userBubble : styles.coachBubble
                  ]}
                >
                  <Text style={styles.senderLabel}>
                    {isUser ? 'Ty' : 'Trener Kowalski'}
                  </Text>
                  <Text style={styles.messageText}>{item.message}</Text>
                </View>
              );
            })
          )}

          {loading && (
            <View style={[styles.messageBubble, styles.coachBubble]}>
              <Text style={styles.senderLabel}>Trener Kowalski</Text>
              <View style={styles.loadingRow}>
                <ActivityIndicator size="small" color="#7DBB5E" />
                <Text style={styles.loadingText}> Analizuję Twój paszport i piszę...</Text>
              </View>
            </View>
          )}
        </ScrollView>

        {/* Quick Prompts */}
        <View style={styles.quickPromptsRow}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {quickPrompts.map((qp, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.chip}
                onPress={() => handleSend(qp.replace(/^[^a-zA-ZĄĆĘŁŃÓŚŹŻąćęłńóśźż]+/g, ''))}
              >
                <Text style={styles.chipText}>{qp}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Input Bar */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.textInput}
            placeholder="Zapytaj trenera..."
            placeholderTextColor="#8E8E93"
            value={input}
            onChangeText={setInput}
            onSubmitEditing={() => handleSend()}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!input.trim() || loading) && styles.sendButtonDisabled]}
            onPress={() => handleSend()}
            disabled={!input.trim() || loading}
          >
            <Text style={styles.sendButtonText}>➔</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121214'
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 16,
    backgroundColor: '#1A1A1E',
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C30'
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2A2A30',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12
  },
  avatarText: {
    fontSize: 20
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF'
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#8E8E93'
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2C2C30',
    alignItems: 'center',
    justifyContent: 'center'
  },
  closeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold'
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 16
  },
  messagesContent: {
    paddingVertical: 16
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 60,
    paddingHorizontal: 30
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12
  },
  emptyTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8
  },
  emptyText: {
    color: '#8E8E93',
    textAlign: 'center',
    fontSize: 14,
    lineHeight: 20
  },
  messageBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 12
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#3B82F6',
    borderBottomRightRadius: 4
  },
  coachBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#26262B',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#33333A'
  },
  senderLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#A1A1AA',
    marginBottom: 4
  },
  messageText: {
    color: '#FFFFFF',
    fontSize: 15,
    lineHeight: 22
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4
  },
  loadingText: {
    color: '#A1A1AA',
    fontSize: 13,
    marginLeft: 6
  },
  quickPromptsRow: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#18181B'
  },
  chip: {
    backgroundColor: '#27272A',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#3F3F46'
  },
  chipText: {
    color: '#E4E4E7',
    fontSize: 13
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#18181B',
    borderTopWidth: 1,
    borderTopColor: '#27272A'
  },
  textInput: {
    flex: 1,
    backgroundColor: '#27272A',
    color: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8
  },
  sendButtonDisabled: {
    backgroundColor: '#3F3F46',
    opacity: 0.5
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold'
  }
});

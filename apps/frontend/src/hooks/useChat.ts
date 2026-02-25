import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, ChatResponse, ExtractedParams, TrafficOverlay } from '../types/scenario';

const WELCOME_MESSAGE: ChatMessage = {
    role: 'assistant',
    content:
        "Ciao! Sono il tuo assistente per la simulazione del traffico a Bari. " +
        "Descrivimi l'evento che vuoi simulare: nome, luogo, data, orario di fine, " +
        "capacità e ospiti VIP. Analizzerò l'impatto sulla mobilità cittadina.",
};

const EMPTY_PARAMS: ExtractedParams = {
    event_name: null,
    venue: null,
    date: null,
    end_time: null,
    capacity: null,
    vip_names: [],
    vip_analysis: null,
    estimated_multiplier: null,
    confidence: null,
};

export function useChat() {
    const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
    const [extractedParams, setExtractedParams] = useState<ExtractedParams>(EMPTY_PARAMS);
    const [readyToSimulate, setReadyToSimulate] = useState(false);
    const [chatLoading, setChatLoading] = useState(false);

    const [trafficOverlay, setTrafficOverlay] = useState<TrafficOverlay | null>(null);
    const [baselineOverlay, setBaselineOverlay] = useState<TrafficOverlay | null>(null);
    const [compareWithBaseline, setCompareWithBaseline] = useState(false);
    const [simulatedDate, setSimulatedDate] = useState<string | null>(null);
    const [selectedHourIndex, setSelectedHourIndex] = useState(0);
    const [simulateLoading, setSimulateLoading] = useState(false);
    const [simulateError, setSimulateError] = useState<string | null>(null);

    const paramsRef = useRef(extractedParams);
    paramsRef.current = extractedParams;

    const sendMessage = useCallback(async (text: string) => {
        const userMsg: ChatMessage = { role: 'user', content: text };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setChatLoading(true);

        try {
            const chatHistory = updatedMessages
                .filter((m) => m !== WELCOME_MESSAGE)
                .map((m) => ({ role: m.role, content: m.content }));

            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data: ChatResponse = await res.json();
            const assistantMsg: ChatMessage = { role: 'assistant', content: data.reply };

            setMessages((prev) => [...prev, assistantMsg]);
            setExtractedParams(data.extracted_params);
            setReadyToSimulate(data.ready_to_simulate);
        } catch (e) {
            const errorMsg: ChatMessage = {
                role: 'assistant',
                content: `Errore di comunicazione: ${e instanceof Error ? e.message : 'riprova.'}`,
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setChatLoading(false);
        }
    }, [messages]);

    const simulateTraffic = useCallback(async () => {
        const p = paramsRef.current;
        if (!p.date || !p.event_name) {
            setSimulateError("Parametri insufficienti. Continua la conversazione con l'IA.");
            return;
        }

        setSimulateLoading(true);
        setSimulateError(null);

        try {
            const body: Record<string, unknown> = {
                event_name: p.event_name,
                capacity: p.capacity || 1000,
                vip_names: p.vip_names,
                date: p.date,
                event_end_time: p.end_time || '22:00',
            };
            if (p.venue) {
                body.event_venue = p.venue;
            }
            if (p.estimated_multiplier != null) {
                body.multiplier = p.estimated_multiplier;
            }

            const res = await fetch('/api/simulate-day', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data: TrafficOverlay = await res.json();
            // #region agent log
            try {
                fetch('http://127.0.0.1:7243/ingest/f65d3bd1-4a59-47f7-8eda-a434091e96ac',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useChat.ts:simulateTraffic',message:'traffic overlay received',data:{hours_count:data?.hours?.length,hours_first5:data?.hours?.slice(0,5),by_street_keys:data?.by_street?Object.keys(data.by_street).slice(0,5):[],has_00:data?.hours?.includes('00:00')},timestamp:Date.now(),hypothesisId:'E'})}).catch(()=>{});
            } catch (_) {}
            // #endregion
            setTrafficOverlay(data);
            setBaselineOverlay(null);
            setCompareWithBaseline(false);
            setSimulatedDate(p.date);
            setSelectedHourIndex(0);
        } catch (e) {
            setSimulateError(e instanceof Error ? e.message : 'Errore simulazione');
            setTrafficOverlay(null);
        } finally {
            setSimulateLoading(false);
        }
    }, []);

    const handleToggleBaseline = useCallback(async () => {
        const date = simulatedDate ?? paramsRef.current.date;
        if (!date) return;

        if (!compareWithBaseline && !baselineOverlay) {
            try {
                const res = await fetch(`/api/baseline?date=${date}`);
                if (!res.ok) throw new Error();
                const data: TrafficOverlay = await res.json();
                setBaselineOverlay(data);
            } catch {
                setBaselineOverlay(null);
                return;
            }
        }
        setCompareWithBaseline((prev) => !prev);
    }, [compareWithBaseline, baselineOverlay, simulatedDate]);

    const effectiveOverlay =
        compareWithBaseline && baselineOverlay ? baselineOverlay : trafficOverlay;

    return {
        messages,
        extractedParams,
        readyToSimulate,
        chatLoading,
        sendMessage,
        trafficOverlay: effectiveOverlay,
        selectedHourIndex,
        setSelectedHourIndex,
        simulateTraffic,
        simulateLoading,
        simulateError,
        compareWithBaseline,
        onToggleBaseline: handleToggleBaseline,
        hasSimulation: !!trafficOverlay,
    };
}

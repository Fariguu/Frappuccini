import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, ExtractedParams } from '../types/scenario';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardHeader, CardFooter } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Send, Bot, User, Loader2, MapPin, Calendar, Clock, Users, Star } from 'lucide-react';

interface ChatSidebarProps {
    messages: ChatMessage[];
    extractedParams: ExtractedParams;
    readyToSimulate: boolean;
    chatLoading: boolean;
    onSendMessage: (text: string) => void;
    onSimulate: () => void;
    simulateLoading: boolean;
    simulateError: string | null;
}

const VipAnalysisBlock: React.FC<{ analysis: string }> = ({ analysis }) => {
    const [expanded, setExpanded] = useState(false);
    const short = analysis.length > 120;

    return (
        <div className="mt-1.5 pt-1.5 border-t border-border/30">
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground block mb-1">
                Analisi VIP
            </span>
            <p className="text-[10px] leading-relaxed text-foreground/80">
                {short && !expanded ? analysis.slice(0, 120) + '...' : analysis}
            </p>
            {short && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-[9px] text-primary font-medium mt-0.5 hover:underline"
                >
                    {expanded ? 'Mostra meno' : 'Mostra tutto'}
                </button>
            )}
        </div>
    );
};

const ParamsSummary: React.FC<{ params: ExtractedParams; ready: boolean }> = ({ params, ready }) => {
    const hasAny = params.event_name || params.venue || params.date || params.capacity;
    if (!hasAny) return null;

    return (
        <Card className="mx-3 mb-3 p-3 bg-accent/5 border-border/50">
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        Parametri Estratti
                    </span>
                    {params.confidence && (
                        <Badge variant={params.confidence === 'high' ? 'default' : 'secondary'} className="text-[9px]">
                            {params.confidence}
                        </Badge>
                    )}
                </div>
                <div className="grid gap-1.5 text-xs">
                    {params.event_name && (
                        <div className="flex items-center gap-2">
                            <Star className="size-3 text-muted-foreground shrink-0" />
                            <span className="font-medium">{params.event_name}</span>
                        </div>
                    )}
                    {params.venue && (
                        <div className="flex items-center gap-2">
                            <MapPin className="size-3 text-muted-foreground shrink-0" />
                            <span>{params.venue}</span>
                        </div>
                    )}
                    {params.date && (
                        <div className="flex items-center gap-2">
                            <Calendar className="size-3 text-muted-foreground shrink-0" />
                            <span>{params.date}</span>
                        </div>
                    )}
                    {params.end_time && (
                        <div className="flex items-center gap-2">
                            <Clock className="size-3 text-muted-foreground shrink-0" />
                            <span>Fine: {params.end_time}</span>
                        </div>
                    )}
                    {params.capacity != null && (
                        <div className="flex items-center gap-2">
                            <Users className="size-3 text-muted-foreground shrink-0" />
                            <span>{params.capacity.toLocaleString('it-IT')} persone</span>
                        </div>
                    )}
                    {params.vip_names.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                            {params.vip_names.map((vip) => (
                                <Badge key={vip} variant="outline" className="text-[9px]">
                                    {vip}
                                </Badge>
                            ))}
                        </div>
                    )}
                    {params.estimated_multiplier != null && (
                        <div className="flex items-center justify-between mt-1 pt-1 border-t border-border/30">
                            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Impatto stimato</span>
                            <Badge
                                variant={params.estimated_multiplier >= 2.5 ? 'destructive' : params.estimated_multiplier >= 1.8 ? 'default' : 'secondary'}
                                className="text-[10px] font-mono"
                            >
                                {params.estimated_multiplier.toFixed(1)}x
                            </Badge>
                        </div>
                    )}
                    {params.vip_analysis && (
                        <VipAnalysisBlock analysis={params.vip_analysis} />
                    )}
                </div>
                {!ready && (
                    <p className="text-[10px] text-muted-foreground italic mt-1">
                        Informazioni mancanti per la simulazione...
                    </p>
                )}
            </div>
        </Card>
    );
};

const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            <Avatar className="size-7 shrink-0 mt-0.5">
                <AvatarFallback className={`text-[10px] font-bold ${isUser ? 'bg-primary text-primary-foreground' : 'bg-accent text-accent-foreground'}`}>
                    {isUser ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
                </AvatarFallback>
            </Avatar>
            <div
                className={`rounded-lg px-3 py-2 text-xs leading-relaxed max-w-[85%] ${
                    isUser
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-white border border-border/50'
                }`}
            >
                {message.content}
            </div>
        </div>
    );
};

const ChatSidebar: React.FC<ChatSidebarProps> = ({
    messages,
    extractedParams,
    readyToSimulate,
    chatLoading,
    onSendMessage,
    onSimulate,
    simulateLoading,
    simulateError,
}) => {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (viewport) {
                viewport.scrollTop = viewport.scrollHeight;
            }
        }
    }, [messages, chatLoading]);

    const handleSend = () => {
        const text = input.trim();
        if (!text || chatLoading) return;
        setInput('');
        onSendMessage(text);
    };

    return (
        <Card className="relative z-10 shrink-0 w-96 h-full rounded-none border-r border-border flex flex-col gap-0 py-0 shadow-sm overflow-hidden bg-white">
            <CardHeader className="p-4 border-b border-border space-y-0">
                <h2 className="text-foreground font-bold tracking-tighter leading-none text-base">
                    TRAFFIC AI
                    <span className="block text-muted-foreground text-[10px] font-medium tracking-normal mt-0.5 italic">
                        Simulatore di traffico assistito da IA
                    </span>
                </h2>
            </CardHeader>

            <ScrollArea ref={scrollRef} className="flex-1 min-h-0">
                <div className="p-3 space-y-3">
                    {messages.map((msg, i) => (
                        <MessageBubble key={i} message={msg} />
                    ))}
                    {chatLoading && (
                        <div className="flex gap-2">
                            <Avatar className="size-7 shrink-0">
                                <AvatarFallback className="bg-accent text-accent-foreground text-[10px]">
                                    <Bot className="size-3.5" />
                                </AvatarFallback>
                            </Avatar>
                            <div className="rounded-lg px-3 py-2 bg-white border border-border/50 flex items-center gap-2 text-xs text-muted-foreground">
                                <Loader2 className="size-3 animate-spin" />
                                Analizzo...
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            <ParamsSummary params={extractedParams} ready={readyToSimulate} />

            <Separator />

            <div className="p-3 space-y-2">
                <div className="flex gap-2">
                    <Input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Descrivi l'evento..."
                        disabled={chatLoading}
                        className="text-foreground bg-white text-xs"
                    />
                    <Button
                        size="icon"
                        onClick={handleSend}
                        disabled={chatLoading || !input.trim()}
                    >
                        <Send className="size-4" />
                    </Button>
                </div>
            </div>

            <CardFooter className="p-3 pt-0 flex flex-col gap-2">
                {simulateError && (
                    <p className="text-[10px] text-destructive font-medium w-full">{simulateError}</p>
                )}
                <Button
                    onClick={onSimulate}
                    disabled={!readyToSimulate || simulateLoading}
                    className="w-full uppercase tracking-widest text-xs"
                >
                    {simulateLoading ? (
                        <>
                            <Loader2 className="size-4 animate-spin" />
                            Simulazione...
                        </>
                    ) : (
                        'Calcola Simulazione'
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default ChatSidebar;

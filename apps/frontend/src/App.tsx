import ChatSidebar from './components/ChatSidebar';
import MapView from './components/MapView';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    extractedParams,
    readyToSimulate,
    chatLoading,
    sendMessage,
    trafficOverlay,
    selectedHourIndex,
    setSelectedHourIndex,
    simulateTraffic,
    simulateLoading,
    simulateError,
    compareWithBaseline,
    onToggleBaseline,
    hasSimulation,
  } = useChat();

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden font-sans">
      <ChatSidebar
        messages={messages}
        extractedParams={extractedParams}
        readyToSimulate={readyToSimulate}
        chatLoading={chatLoading}
        onSendMessage={sendMessage}
        onSimulate={simulateTraffic}
        simulateLoading={simulateLoading}
        simulateError={simulateError}
        compareWithBaseline={compareWithBaseline}
        onToggleBaseline={onToggleBaseline}
        hasSimulation={hasSimulation}
      />
      <main className="flex-1 relative flex flex-col h-full overflow-hidden">
        <MapView
          trafficOverlay={trafficOverlay}
          selectedHourIndex={selectedHourIndex}
          onHourChange={setSelectedHourIndex}
        />
      </main>
    </div>
  );
}

export default App;

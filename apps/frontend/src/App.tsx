import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import { useScenario } from './hooks/useScenario';

function App() {
  const {
    scenario,
    updateEvent,
    updatePrivateTransport,
    togglePublicIntegration,
    addRouteStop,
    clearRoute,
    generateJson
  } = useScenario();

  const handleTest = () => {
    alert('Test button clicked! Current participants: ' + scenario.event.totalPeople);
  };

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden font-sans">
      <Sidebar
        scenario={scenario}
        onUpdateEvent={updateEvent}
        onUpdatePrivate={updatePrivateTransport}
        onTogglePublic={togglePublicIntegration}
        onGenerate={generateJson}
        onClearRoute={clearRoute}
        onTest={handleTest}
      />
      <main className="flex-1 relative flex flex-col h-full overflow-hidden">
        <MapView
          scenario={scenario}
          onMapClick={addRouteStop}
        />
      </main>
    </div>
  );
}

export default App;

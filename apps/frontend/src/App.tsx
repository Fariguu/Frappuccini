import { useState } from 'react';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';

function App() {
  const [eventParam, setEventParam] = useState('');
  const [intensity, setIntensity] = useState(50);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Control Panel (Sidebar) */}
      <Sidebar
        eventParam={eventParam}
        setEventParam={setEventParam}
        intensity={intensity}
        setIntensity={setIntensity}
      />

      {/* Main Map View */}
      <main className="flex-1 h-full overflow-hidden">
        <MapView intensity={intensity} />
      </main>
    </div>
  );
}

export default App;

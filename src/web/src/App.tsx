import { useCallback, useEffect, useState } from "react";
import Header, { type Tab } from "./components/Header";
import ProducerForm from "./components/ProducerForm";
import FarmForm from "./components/FarmForm";
import MapPage from "./pages/MapPage";
import { listProducers, type Producer } from "./services/api";
import "./styles/App.css";

export default function App() {
  const [tab, setTab] = useState<Tab>("forms");
  const [producers, setProducers] = useState<Producer[]>([]);

  const refresh = useCallback(() => {
    listProducers().then(setProducers).catch(() => setProducers([]));
  }, []);

  useEffect(refresh, [refresh]);

  return (
    <div className="app">
      <Header tab={tab} onChange={setTab} />
      <main className="main">
        {tab === "forms" ? (
          <div className="forms-grid">
            <ProducerForm onCreated={refresh} />
            <FarmForm producers={producers} />
          </div>
        ) : (
          <MapPage />
        )}
      </main>
    </div>
  );
}
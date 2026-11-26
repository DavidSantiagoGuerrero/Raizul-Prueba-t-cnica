import "../styles/Header.css";

export type Tab = "forms" | "map";

interface Props {
  tab: Tab;
  onChange: (tab: Tab) => void;
}

const TABS: { id: Tab; label: string }[] = [
  { id: "forms", label: "Formularios" },
  { id: "map", label: "Mapa" },
];

export default function Header({ tab, onChange }: Props) {
  return (
    <header className="header">
      <h1 className="header-title">Productores de cacao</h1>
      <nav className="header-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "tab tab-active" : "tab"}
            onClick={() => onChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
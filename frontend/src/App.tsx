import { useState } from "react";
import "./App.css";
import { useDocumentTitle } from "./hooks/useDocumentTitle";
import { usePokemonCatalog } from "./hooks/usePokemonCatalog";
import { HomePage } from "./pages/HomePage";
import { TeamsPage } from "./pages/TeamsPage";

type Tab = "pokedex" | "teams";

const TAB_TITLES: Record<Tab, string> = {
  pokedex: "Pokedex",
  teams: "Teams",
};

function App() {
  const [tab, setTab] = useState<Tab>("pokedex");
  const catalog = usePokemonCatalog();
  useDocumentTitle(TAB_TITLES[tab]);

  return (
    <>
      <nav className="app-nav">
        <button
          type="button"
          className={`app-nav__tab${tab === "pokedex" ? " app-nav__tab--active" : ""}`}
          onClick={() => setTab("pokedex")}
        >
          Pokedex
        </button>
        <button
          type="button"
          className={`app-nav__tab${tab === "teams" ? " app-nav__tab--active" : ""}`}
          onClick={() => setTab("teams")}
        >
          Teams
        </button>
      </nav>
      {tab === "pokedex" ? <HomePage catalog={catalog} /> : <TeamsPage catalog={catalog} />}
    </>
  );
}

export default App;

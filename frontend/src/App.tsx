import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { usePokemonCatalog } from "./hooks/usePokemonCatalog";
import { HomePage } from "./pages/HomePage";
import { TeamsPage } from "./pages/TeamsPage";

function App() {
  const catalog = usePokemonCatalog();

  return (
    <>
      <nav className="app-nav">
        <span className="app-nav__brand">Pokétactics</span>
        <div className="app-nav__tabs">
          <NavLink
            to="/pokedex"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Pokédex
          </NavLink>
          <NavLink
            to="/teams"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Teams
          </NavLink>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/pokedex" replace />} />
        <Route path="/pokedex" element={<HomePage catalog={catalog} />} />
        <Route path="/teams" element={<TeamsPage catalog={catalog} />} />
        <Route path="*" element={<Navigate to="/pokedex" replace />} />
      </Routes>
    </>
  );
}

export default App;

import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { useMoveCatalog } from "./hooks/useMoveCatalog";
import { usePokemonCatalog } from "./hooks/usePokemonCatalog";
import { HomePage } from "./pages/HomePage";
import { MoveDetailPage } from "./pages/MoveDetailPage";
import { MovesPage } from "./pages/MovesPage";
import { PokemonDetailPage } from "./pages/PokemonDetailPage";
import { TeamsPage } from "./pages/TeamsPage";

function App() {
  const catalog = usePokemonCatalog();
  const moveCatalog = useMoveCatalog();

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
            to="/moves"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Moves
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
        <Route path="/moves" element={<MovesPage catalog={moveCatalog} />} />
        <Route path="/moves/:idOrName" element={<MoveDetailPage />} />
        <Route path="/pokemon/:idOrName" element={<PokemonDetailPage />} />
        <Route path="/teams" element={<TeamsPage catalog={catalog} />} />
        <Route path="*" element={<Navigate to="/pokedex" replace />} />
      </Routes>
    </>
  );
}

export default App;

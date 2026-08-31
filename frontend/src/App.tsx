import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { AlertBanner } from "./components/AlertBanner";
import { useMoveCatalog } from "./hooks/useMoveCatalog";
import { usePokemonCatalog } from "./hooks/usePokemonCatalog";
import { ChangeLogPage } from "./pages/ChangeLogPage";
import { DevToolsPage } from "./pages/DevToolsPage";
import { HomePage } from "./pages/HomePage";
import { MoveDetailPage } from "./pages/MoveDetailPage";
import { MovesPage } from "./pages/MovesPage";
import { PokemonDetailPage } from "./pages/PokemonDetailPage";
import { TeamDetailPage } from "./pages/TeamDetailPage";
import { TeamEditPage } from "./pages/TeamEditPage";
import { TeamOptimizerPage } from "./pages/TeamOptimizerPage";
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
          <NavLink
            to="/optimizer"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Team Optimizer
          </NavLink>
          <NavLink
            to="/changes"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Change Log
          </NavLink>
          <NavLink
            to="/dev-tools"
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Dev Tools
          </NavLink>
        </div>
      </nav>
      <AlertBanner catalog={catalog} moveCatalog={moveCatalog} />
      <Routes>
        <Route path="/" element={<Navigate to="/pokedex" replace />} />
        <Route path="/pokedex" element={<HomePage catalog={catalog} />} />
        <Route path="/moves" element={<MovesPage catalog={moveCatalog} />} />
        <Route path="/moves/:idOrName" element={<MoveDetailPage />} />
        <Route path="/pokemon/:idOrName" element={<PokemonDetailPage />} />
        <Route path="/teams" element={<TeamsPage />} />
        <Route
          path="/teams/new"
          element={<TeamEditPage catalog={catalog} moveCatalog={moveCatalog} />}
        />
        <Route path="/teams/:teamId" element={<TeamDetailPage />} />
        <Route
          path="/teams/:teamId/edit"
          element={<TeamEditPage catalog={catalog} moveCatalog={moveCatalog} />}
        />
        <Route
          path="/optimizer"
          element={<TeamOptimizerPage catalog={catalog} moveCatalog={moveCatalog} />}
        />
        <Route
          path="/changes"
          element={<ChangeLogPage catalog={catalog} moveCatalog={moveCatalog} />}
        />
        <Route
          path="/dev-tools"
          element={<DevToolsPage catalog={catalog} moveCatalog={moveCatalog} />}
        />
        <Route path="*" element={<Navigate to="/pokedex" replace />} />
      </Routes>
    </>
  );
}

export default App;

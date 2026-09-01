import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { AlertBanner } from "./components/AlertBanner";
import { useMoveCatalog } from "./hooks/useMoveCatalog";
import { usePokemonCatalog } from "./hooks/usePokemonCatalog";
import { ChangeLogPage } from "./pages/ChangeLogPage";
import { DevToolsPage } from "./pages/DevToolsPage";
import { LandingPage } from "./pages/LandingPage";
import { MoveDetailPage } from "./pages/MoveDetailPage";
import { MovesPage } from "./pages/MovesPage";
import { PokedexPage } from "./pages/PokedexPage";
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
            to="/"
            end
            className={({ isActive }) => `app-nav__tab${isActive ? " app-nav__tab--active" : ""}`}
          >
            Home
          </NavLink>
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
        <Route path="/" element={<LandingPage />} />
        <Route path="/pokedex" element={<PokedexPage catalog={catalog} />} />
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;

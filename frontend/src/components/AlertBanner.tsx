import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { dismissAlert, fetchAlerts } from "../api/alerts";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Alert } from "../types/alert";
import { DamageClassIcon } from "./DamageClassIcon";
import "./AlertBanner.css";

const POLL_INTERVAL_MS = 30_000;

interface AlertBannerProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

/** Mounted globally (see App.tsx) so a fresh alert — e.g. from triggering a
 * scan live during a demo — surfaces no matter which page the user is on.
 * Polls rather than fetching once, since alerts can appear at any time
 * without any user action to hang a refetch off of. */
export function AlertBanner({ catalog, moveCatalog }: AlertBannerProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    let cancelled = false;
    function load() {
      fetchAlerts()
        .then((data) => {
          if (!cancelled) setAlerts(data);
        })
        .catch(() => {
          // Alerts are a nice-to-have banner, not core functionality — a
          // failed fetch just means no banner shows, not an error state.
        });
    }
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  async function handleDismiss(alertId: number) {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    try {
      await dismissAlert(alertId);
    } catch {
      // Best-effort: if this fails the alert just reappears on the next
      // poll, an acceptable fallback for a non-critical UI action.
    }
  }

  // Wait for both catalogs too, not just the (much smaller, faster) alerts
  // fetch — otherwise the banner renders with bare text first and "pops in"
  // the sprite/move info a few seconds later once they resolve, which reads
  // as a bug rather than a loading state.
  if (catalog.status !== "ready" || moveCatalog.status !== "ready" || alerts.length === 0) {
    return null;
  }

  return (
    <div className="alert-banner">
      {alerts.map((alert) => {
        const pokemon = catalog.pokemon.find((p) => p.id === alert.pokemon_id);
        const move = alert.move_id
          ? moveCatalog.moves.find((m) => m.id === alert.move_id)
          : undefined;
        return (
          <div className="alert-banner__item" key={alert.id}>
            {pokemon && (
              <img className="alert-banner__sprite" src={pokemon.sprite_url} alt={pokemon.name} />
            )}
            <span className="alert-banner__text">
              {pokemon && (
                <Link to={`/pokemon/${pokemon.name}`} className="alert-banner__pokemon-name">
                  {pokemon.name.replace(/-/g, " ")}
                </Link>
              )}{" "}
              {alert.message}
              {move && (
                <>
                  {" ("}
                  <Link to={`/moves/${move.name}`} className="alert-banner__move-link">
                    <DamageClassIcon damageClass={move.damage_class} size={13} />
                    {move.name.replace(/-/g, " ")}
                  </Link>
                  {")"}
                </>
              )}
            </span>
            <button
              type="button"
              className="alert-banner__dismiss"
              onClick={() => handleDismiss(alert.id)}
              aria-label="Dismiss alert"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}

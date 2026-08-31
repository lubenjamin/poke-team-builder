import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import {
  MOVE_NUMERIC_FIELDS,
  POKEMON_NUMERIC_FIELDS,
  corruptMoveStat,
  corruptPokemonMovepool,
  corruptPokemonStat,
  scanMoves,
  scanPokemon,
  verifyInternalSecret,
  type MoveNumericField,
  type PokemonNumericField,
} from "../api/devTools";
import { PageHero } from "../components/PageHero";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useInternalSecret } from "../hooks/useInternalSecret";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { ScanResult } from "../types/scan";
import "./DevToolsPage.css";

interface DevToolsPageProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

/** Demo/testing surface: trigger either scan on demand, and deliberately
 * corrupt a cached numeric stat to simulate PokeAPI drift, so the change-log
 * + alerting + team-auto-repair behavior can be demonstrated live without
 * waiting for a real upstream change. Gated by the same internal secret as
 * the production cron trigger — entered once, kept in sessionStorage. */
export function DevToolsPage({ catalog, moveCatalog }: DevToolsPageProps) {
  useDocumentTitle("Dev Tools");
  const { secret, setSecret, clearSecret } = useInternalSecret();
  const [secretInput, setSecretInput] = useState("");
  const [verifyStatus, setVerifyStatus] = useState<"idle" | "verifying" | "error">("idle");

  if (!secret) {
    async function handleSubmit(e: FormEvent) {
      e.preventDefault();
      const trimmed = secretInput.trim();
      if (!trimmed) return;
      setVerifyStatus("verifying");
      try {
        await verifyInternalSecret(trimmed);
        setSecret(trimmed); // only store + unlock the page once the backend confirms it's correct
      } catch {
        setVerifyStatus("error");
      }
    }

    return (
      <main>
        <PageHero
          title="Dev Tools"
          description="Trigger scans and simulate data drift for demoing the change-detection pipeline."
        />
        <form className="dev-tools__secret-form" onSubmit={handleSubmit}>
          <label className="dev-tools__secret-label">
            Internal secret required
            <input
              type="password"
              value={secretInput}
              onChange={(e) => {
                setSecretInput(e.target.value);
                setVerifyStatus("idle");
              }}
              placeholder="Paste the internal API secret"
              autoFocus
            />
          </label>
          <button type="submit" disabled={!secretInput.trim() || verifyStatus === "verifying"}>
            {verifyStatus === "verifying" ? "Checking..." : "Save"}
          </button>
          {verifyStatus === "error" && (
            <p className="dev-tools__error">Incorrect secret.</p>
          )}
        </form>
      </main>
    );
  }

  return (
    <main>
      <PageHero
        title="Dev Tools"
        description="Trigger scans and simulate data drift for demoing the change-detection pipeline."
      />
      <div className="dev-tools__grid">
        <ScanCard title="Scan Pokémon" onScan={scanPokemon} onUnauthorized={clearSecret} />
        <ScanCard title="Scan Moves" onScan={scanMoves} onUnauthorized={clearSecret} />
        <CorruptPokemonCard catalog={catalog} onUnauthorized={clearSecret} />
        <CorruptMoveCard moveCatalog={moveCatalog} onUnauthorized={clearSecret} />
        <CorruptMovepoolCard
          catalog={catalog}
          moveCatalog={moveCatalog}
          onUnauthorized={clearSecret}
        />
      </div>
    </main>
  );
}

interface ScanCardProps {
  title: string;
  onScan: (limit?: number) => Promise<ScanResult>;
  onUnauthorized: () => void;
}

function ScanCard({ title, onScan, onUnauthorized }: ScanCardProps) {
  const [limit, setLimit] = useState("");
  const [status, setStatus] = useState<"idle" | "running" | "error">("idle");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setStatus("running");
    setError(null);
    try {
      const parsedLimit = limit.trim() ? Number(limit) : undefined;
      const data = await onScan(parsedLimit);
      setResult(data);
      setStatus("idle");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      setError(err instanceof ApiError ? err.message : "Scan failed");
      setStatus("error");
    }
  }

  return (
    <section className="dev-tools__card">
      <h2>{title}</h2>
      <label className="dev-tools__field">
        Limit (optional)
        <input
          type="number"
          min={1}
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
          placeholder="Full catalog if blank"
        />
      </label>
      <button type="button" onClick={handleRun} disabled={status === "running"}>
        {status === "running" ? "Scanning..." : "Run scan"}
      </button>
      {error && <p className="dev-tools__error">{error}</p>}
      {result && (
        <dl className="dev-tools__result">
          <div>
            <dt>Scanned</dt>
            <dd>{result.scanned}</dd>
          </div>
          <div>
            <dt>Changed</dt>
            <dd>{result.changed}</dd>
          </div>
          <div>
            <dt>Change-log rows</dt>
            <dd>{result.changes_logged}</dd>
          </div>
          <div>
            <dt>Alerts created</dt>
            <dd>{result.alerts_created}</dd>
          </div>
          <div>
            <dt>Fetch failed</dt>
            <dd>{result.fetch_failed}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}

interface CorruptPokemonCardProps {
  catalog: PokemonCatalog;
  onUnauthorized: () => void;
}

function CorruptPokemonCard({ catalog, onUnauthorized }: CorruptPokemonCardProps) {
  const sorted = [...catalog.pokemon].sort((a, b) => a.name.localeCompare(b.name));
  const [pokemonId, setPokemonId] = useState<number | "">("");
  const [field, setField] = useState<PokemonNumericField>("hp");
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleApply() {
    if (pokemonId === "" || !value.trim()) return;
    setStatus("saving");
    setError(null);
    try {
      await corruptPokemonStat(pokemonId, field, Number(value));
      setStatus("done");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      setError(err instanceof ApiError ? err.message : "Update failed");
      setStatus("error");
    }
  }

  return (
    <section className="dev-tools__card">
      <h2>Corrupt a Pokémon stat</h2>
      <label className="dev-tools__field">
        Pokémon
        <select
          value={pokemonId}
          onChange={(e) => setPokemonId(e.target.value ? Number(e.target.value) : "")}
        >
          <option value="">Select a Pokémon...</option>
          {sorted.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
      <label className="dev-tools__field">
        Field
        <select value={field} onChange={(e) => setField(e.target.value as PokemonNumericField)}>
          {POKEMON_NUMERIC_FIELDS.map((f) => (
            <option key={f} value={f}>
              {f.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </label>
      <label className="dev-tools__field">
        New value
        <input type="number" value={value} onChange={(e) => setValue(e.target.value)} />
      </label>
      <button type="button" onClick={handleApply} disabled={status === "saving"}>
        {status === "saving" ? "Applying..." : "Apply"}
      </button>
      {status === "done" && <p className="dev-tools__success">Updated.</p>}
      {error && <p className="dev-tools__error">{error}</p>}
    </section>
  );
}

interface CorruptMovepoolCardProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
  onUnauthorized: () => void;
}

function CorruptMovepoolCard({ catalog, moveCatalog, onUnauthorized }: CorruptMovepoolCardProps) {
  const sortedPokemon = [...catalog.pokemon].sort((a, b) => a.name.localeCompare(b.name));
  const sortedMoves = [...moveCatalog.moves].sort((a, b) => a.name.localeCompare(b.name));
  const [pokemonId, setPokemonId] = useState<number | "">("");
  const [moveId, setMoveId] = useState<number | "">("");
  const [status, setStatus] = useState<"idle" | "saving" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleApply() {
    if (pokemonId === "" || moveId === "") return;
    setStatus("saving");
    setError(null);
    try {
      await corruptPokemonMovepool(pokemonId, moveId);
      setStatus("done");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      setError(err instanceof ApiError ? err.message : "Update failed");
      setStatus("error");
    }
  }

  return (
    <section className="dev-tools__card">
      <h2>Corrupt a Pokémon's move pool</h2>
      <p className="dev-tools__hint">
        Adds a move to this Pokémon's cached move pool that PokeAPI doesn't actually list. Assign
        it to a team via the Team Builder, then run a Pokémon scan — the move gets detected as no
        longer learnable, unassigned from the team, and the owner alerted.
      </p>
      <label className="dev-tools__field">
        Pokémon
        <select
          value={pokemonId}
          onChange={(e) => setPokemonId(e.target.value ? Number(e.target.value) : "")}
        >
          <option value="">Select a Pokémon...</option>
          {sortedPokemon.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
      <label className="dev-tools__field">
        Move to add
        <select
          value={moveId}
          onChange={(e) => setMoveId(e.target.value ? Number(e.target.value) : "")}
        >
          <option value="">Select a move...</option>
          {sortedMoves.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </label>
      <button type="button" onClick={handleApply} disabled={status === "saving"}>
        {status === "saving" ? "Applying..." : "Apply"}
      </button>
      {status === "done" && <p className="dev-tools__success">Added.</p>}
      {error && <p className="dev-tools__error">{error}</p>}
    </section>
  );
}

interface CorruptMoveCardProps {
  moveCatalog: MoveCatalog;
  onUnauthorized: () => void;
}

function CorruptMoveCard({ moveCatalog, onUnauthorized }: CorruptMoveCardProps) {
  const sorted = [...moveCatalog.moves].sort((a, b) => a.name.localeCompare(b.name));
  const [moveId, setMoveId] = useState<number | "">("");
  const [field, setField] = useState<MoveNumericField>("power");
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleApply() {
    if (moveId === "" || !value.trim()) return;
    setStatus("saving");
    setError(null);
    try {
      await corruptMoveStat(moveId, field, Number(value));
      setStatus("done");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      setError(err instanceof ApiError ? err.message : "Update failed");
      setStatus("error");
    }
  }

  return (
    <section className="dev-tools__card">
      <h2>Corrupt a move stat</h2>
      <label className="dev-tools__field">
        Move
        <select value={moveId} onChange={(e) => setMoveId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Select a move...</option>
          {sorted.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </label>
      <label className="dev-tools__field">
        Field
        <select value={field} onChange={(e) => setField(e.target.value as MoveNumericField)}>
          {MOVE_NUMERIC_FIELDS.map((f) => (
            <option key={f} value={f}>
              {f.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </label>
      <label className="dev-tools__field">
        New value
        <input type="number" value={value} onChange={(e) => setValue(e.target.value)} />
      </label>
      <button type="button" onClick={handleApply} disabled={status === "saving"}>
        {status === "saving" ? "Applying..." : "Apply"}
      </button>
      {status === "done" && <p className="dev-tools__success">Updated.</p>}
      {error && <p className="dev-tools__error">{error}</p>}
    </section>
  );
}

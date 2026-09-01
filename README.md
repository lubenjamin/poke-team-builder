# Pokétactics

An end-to-end Pokémon team builder: browse the full Pokédex, build and manage
multiple teams, generate a matchup-aware counter team for any roster, and get
alerted when a Pokémon on one of your teams changes in the underlying data.
React/Vite frontend, FastAPI backend, Postgres, PokeAPI as the data source.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite | Static build, fast dev loop, no server-rendering complexity this app doesn't need. |
| Backend | Python + FastAPI | Typed request/response models via Pydantic, and a natural home for both the HTTP API and the scheduled ingestion job in one codebase. |
| Database | Postgres (Neon) | Neon's free tier is permanent and needs no card, unlike alternatives that expire after 30 days — a real risk to plan around ahead of a deadline. Trade-off: idle compute suspends, so the first query after idle eats a resume penalty; acceptable here since this isn't a latency-critical app. |
| Identity | Anonymous client ID (`X-Client-Id`, generated client-side, sent on every request) | The requirement is "persist across sessions," not cross-device login. Full auth (hashing, JWT, login UI) would cost hours for something the spec doesn't ask for — this is a scoped trade-off, not an oversight. |
| Ingestion | One shared `fetch → transform → validate → write` pipeline, used by both the one-time batch load and the recurring scan | Guarantees the two entry points can never validate data differently, and keeps "reject a bad record, log it, keep going" logic in exactly one place. |
| Scheduling | GitHub Actions cron → internal API endpoint | Free, and the run logs double as demo evidence that the freshness feature actually executes on a schedule, not just in code. |

## Design decisions worth calling out

**Species vs. form is a real split in the data model, not a simplification.**
PokeAPI's `/pokemon` catalog has ~1343 entries, but only ~1025 are distinct
national-dex species — the rest are alternate forms (Rotom's five appliance
forms, regional variants, Mega/Primal forms) that share a dex number with
their base species. The schema reflects this directly: `pokemon_species` is
one row per dex entry, `pokemon` is one row per *form*, and every "pokedex
number" shown anywhere in the app is resolved through that relationship —
never assumed to equal a form's own ID.

**Pokémon and move data get different scan functions because they have
different real-world change cadences.** In the actual games, movesets and
base stats get balance-patched on their own schedules, independent of each
other — so `scan_all_pokemon_for_changes` and `scan_all_moves_for_changes`
are separate, independently schedulable jobs rather than one combined scan,
even though they share the same underlying pipeline.

**`is_battle_only` and species identity are treated as immutable, fetched
once at batch-load time, not on every recurring scan.** Whether a form is
battle-only (a Mega Evolution, a Primal Reversion) is a structural fact about
that form, not something that gets balance-patched — unlike a base stat or a
movepool entry, which can. Re-fetching it on every scan would double the
per-item request cost of every future scan, forever, to protect against a
change that structurally can't happen. This is a deliberate cost/coverage
trade-off, not an oversight.

**Alerts are filtered by current team membership at read time, not fixed at
write time.** If a user removes the affected Pokémon from a team, the alert
stops showing — but the change-log entry itself stays, visible in the public
change log. Re-add the Pokémon within the 7-day window and the alert reappears
automatically, with no extra bookkeeping.

**Ingestion fails closed.** A malformed record is rejected, logged with its
raw payload, and skipped — the last-known-good cached value is left
untouched, and one bad record never aborts the rest of a batch or scan.

## The counter-team generator is a deliberately simplified model — not a battle simulator

The generator scores every legal candidate's stats and movepool against a
fixed opponent roster, greedily assembles a 6-Pokémon team out of those
scores with a penalty for redundant typing, then greedily fills each
teammate's moveset for coverage. It's useful as a *relative ranking signal*,
and it's worth being explicit about what it can't see, because the gap is
informative rather than incidental:

- **No EVs, IVs, natures, abilities, or held items.** Every stat used in the
  damage formula is a Pokémon's raw base stat — there's no stat variance, no
  nature modifier, no ability interaction (Intimidate, weather, terrain), and
  no item effect (Choice Scarf, Life Orb, Focus Sash). Two real teams built
  around the same six species can play out completely differently depending
  on these; this generator can't distinguish them at all.
- **A core part of team-building is synergy *within* your own team, not just
  finding Pokémon that individually do the most damage to the opponent.**
  Real team-building is as much about how six Pokémon support each other as
  it is about any one of them being strong on paper. A common example is the
  "utility" Pokémon — a team commonly carries one or two slots that aren't
  there to deal damage at all: Tailwind for a speed swing, redirection to
  protect a sweeper, status spreading, hazard control, healing. Their value
  is entirely relational — they're worth having *because of how they enable
  a specific teammate*, not because of anything measurable about them in
  isolation.

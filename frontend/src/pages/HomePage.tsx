import { PokedexTable } from "../components/PokedexTable";

export function HomePage() {
  return (
    <main>
      <h1 className="page-title">Pokedex</h1>
      <PokedexTable />
    </main>
  );
}

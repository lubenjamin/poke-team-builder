import { PageHero } from "../components/PageHero";
import { PokedexTable } from "../components/PokedexTable";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";

interface PokedexPageProps {
  catalog: PokemonCatalog;
}

export function PokedexPage({ catalog }: PokedexPageProps) {
  useDocumentTitle("Pokédex");

  return (
    <main>
      <PageHero
        title="National Pokédex"
        description=""
      />
      <PokedexTable catalog={catalog} />
    </main>
  );
}

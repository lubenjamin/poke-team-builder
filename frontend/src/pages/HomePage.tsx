import { PageHero } from "../components/PageHero";
import { PokedexTable } from "../components/PokedexTable";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";

interface HomePageProps {
  catalog: PokemonCatalog;
}

export function HomePage({ catalog }: HomePageProps) {
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

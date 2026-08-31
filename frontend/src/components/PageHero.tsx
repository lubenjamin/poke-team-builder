import "./PageHero.css";

interface PageHeroProps {
  title: string;
  description: string;
}

export function PageHero({ title, description }: PageHeroProps) {
  return (
    <div className="page-hero">
      <h1 className="page-hero__title">{title}</h1>
      {description && <p className="page-hero__description">{description}</p>}
    </div>
  );
}

import { useEffect } from "react";

const APP_NAME = "Pokétactics";

export function useDocumentTitle(section: string): void {
  useEffect(() => {
    document.title = `${section} · ${APP_NAME}`;
  }, [section]);
}

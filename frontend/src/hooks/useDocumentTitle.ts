import { useEffect } from "react";

const APP_NAME = "Poké Team Builder";

export function useDocumentTitle(section: string): void {
  useEffect(() => {
    document.title = `${section} · ${APP_NAME}`;
  }, [section]);
}

const NAVIGATION_EXPANDED_KEY = "dojo.navigation-rail-expanded";

export function readNavigationExpanded(): boolean {
  if (typeof window === "undefined") return false;

  try {
    return window.localStorage.getItem(NAVIGATION_EXPANDED_KEY) === "true";
  } catch {
    return false;
  }
}

export function writeNavigationExpanded(expanded: boolean): void {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(NAVIGATION_EXPANDED_KEY, String(expanded));
  } catch {
    // A blocked storage area should not prevent navigation from working.
  }
}

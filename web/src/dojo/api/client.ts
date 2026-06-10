export type AppStatus = {
  app: string;
  ready: boolean;
  mode: string;
};

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export async function fetchAppStatus(): Promise<AppStatus> {
  const response = await fetch(`${apiBaseUrl}/api/app/status`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as AppStatus;
}

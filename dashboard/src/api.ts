import type { Opportunity } from "./types";

const BASE_URL = "http://localhost:8000";

export async function scanNow(bankroll: number): Promise<Opportunity[]> {
  const response = await fetch(`${BASE_URL}/scan?bankroll=${bankroll}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Scan failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchArbitrage(): Promise<Opportunity[]> {
  const response = await fetch(`${BASE_URL}/arbitrage`);
  if (!response.ok) {
    throw new Error(`Failed to fetch arbitrage: ${response.status}`);
  }
  return response.json();
}

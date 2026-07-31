import { useMemo, useState } from "react";
import { scanNow } from "./api";
import type { Opportunity } from "./types";
import { OpportunityCard } from "./components/OpportunityCard";

function App() {
  const [bankroll, setBankroll] = useState(1000);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [minProfit, setMinProfit] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleScan() {
    setLoading(true);
    setError(null);
    try {
      const results = await scanNow(bankroll);
      setOpportunities(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  const visibleOpportunities = useMemo(() => {
    return opportunities
      .filter((o) => o.roi_percentage >= minProfit)
      .sort((a, b) => b.roi_percentage - a.roi_percentage);
  }, [opportunities, minProfit]);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-bold">NBA Arbitrage Scanner</h1>

      <div className="mt-4 flex flex-wrap items-end gap-4">
        <label className="flex flex-col text-sm">
          Bankroll
          <input
            type="number"
            className="mt-1 w-32 rounded border border-gray-300 p-2"
            value={bankroll}
            onChange={(e) => setBankroll(Number(e.target.value))}
          />
        </label>

        <label className="flex flex-col text-sm">
          Min profit %
          <input
            type="number"
            className="mt-1 w-32 rounded border border-gray-300 p-2"
            value={minProfit}
            onChange={(e) => setMinProfit(Number(e.target.value))}
          />
        </label>

        <button
          onClick={handleScan}
          disabled={loading}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "Scanning..." : "Scan Now"}
        </button>
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <h2 className="mt-8 text-lg font-semibold">Active Opportunities</h2>
      <div className="mt-3 flex flex-col gap-3">
        {visibleOpportunities.length === 0 && (
          <p className="text-gray-500">No opportunities yet — click Scan Now.</p>
        )}
        {visibleOpportunities.map((o) => (
          <OpportunityCard key={`${o.game}-${o.sportsbook_a}-${o.sportsbook_b}`} opportunity={o} />
        ))}
      </div>
    </div>
  );
}

export default App;

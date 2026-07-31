import type { Opportunity } from "../types";

function oddsAgeLabel(timestamp: string): string {
  const ageSeconds = (Date.now() - new Date(timestamp).getTime()) / 1000;
  if (ageSeconds < 60) return `${Math.floor(ageSeconds)}s ago`;
  return `${Math.floor(ageSeconds / 60)}m ago`;
}

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const isStrong = opportunity.roi_percentage >= 3;

  return (
    <div className={`rounded-lg border p-4 shadow-sm ${isStrong ? "border-green-400 bg-green-50" : "border-gray-200 bg-white"}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🏀 {opportunity.game}</h3>
        <span className="text-sm text-gray-500">{oddsAgeLabel(opportunity.timestamp)}</span>
      </div>

      <div className="mt-1 flex gap-4 text-sm">
        <span className="font-medium text-green-700">ROI {opportunity.roi_percentage.toFixed(1)}%</span>
        <span className="text-gray-600">Guaranteed profit ${opportunity.guaranteed_profit.toFixed(2)}</span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded border border-gray-100 p-2">
          <div className="font-semibold">{opportunity.sportsbook_a}</div>
          <div>{opportunity.selection_a}</div>
          <div>Odds: {opportunity.odds_a}</div>
          <div>Stake: ${opportunity.stake_a.toFixed(2)}</div>
        </div>
        <div className="rounded border border-gray-100 p-2">
          <div className="font-semibold">{opportunity.sportsbook_b}</div>
          <div>{opportunity.selection_b}</div>
          <div>Odds: {opportunity.odds_b}</div>
          <div>Stake: ${opportunity.stake_b.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}

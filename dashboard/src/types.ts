export interface Opportunity {
  game: string;
  market: string;
  sportsbook_a: string;
  selection_a: string;
  odds_a: number;
  stake_a: number;
  sportsbook_b: string;
  selection_b: string;
  odds_b: number;
  stake_b: number;
  arbitrage_percentage: number;
  roi_percentage: number;
  guaranteed_return: number;
  guaranteed_profit: number;
  timestamp: string;
}

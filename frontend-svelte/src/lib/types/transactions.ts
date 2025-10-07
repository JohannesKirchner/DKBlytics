export interface Transaction {
  id?: string; public_id?: string;
  date: string;                       // YYYY-MM-DD
  account_id: string;
  account_name?: string | null;
  entity?: string | null;
  text?: string | null;
  category?: string | null;
  category_name?: string | null;
  /** Money comes as string from API */
  amount: string;
}
export interface Account {
  public_id: string;
  name: string;
  holder_name: string;
  /** Money comes as string from API */
  balance: string;
}
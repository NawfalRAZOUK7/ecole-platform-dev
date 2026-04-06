export interface FeedItem {
  id: string;
  school_id?: string | null;
  item_type: string;
  title: string;
  summary: string | null;
  reference_type: string | null;
  reference_id: string | null;
  published_at: string;
  action_url?: string | null;
  body?: string | null;
}

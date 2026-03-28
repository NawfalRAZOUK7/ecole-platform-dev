export interface FeedItem {
  id: string;
  school_id: string;
  item_type: string;
  title: string;
  summary: string | null;
  reference_type: string | null;
  reference_id: string | null;
  published_at: string;
}

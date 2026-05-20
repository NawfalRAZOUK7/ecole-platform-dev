export interface SchoolSettings {
  id: string;
  name: string;
  branding?: {
    primary_color?: string;
    logo_url?: string | null;
  };
  features?: Record<string, boolean>;
}

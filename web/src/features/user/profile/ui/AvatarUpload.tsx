import type { AvatarUploadProps } from '../model/profile.types';

export function AvatarUpload({ fullName }: AvatarUploadProps) {
  return (
    <div className="profile-avatar" aria-label={fullName}>
      <span style={{ fontSize: '48px' }}>👤</span>
    </div>
  );
}

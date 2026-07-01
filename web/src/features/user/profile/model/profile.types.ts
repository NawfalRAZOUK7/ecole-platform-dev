import type { FormEvent } from 'react';
import type { UserProfile } from '@/app/providers/AuthContext';
import type { ChildEntry, ProfileResponse } from '../api/profile.api';

export interface AvatarUploadProps {
  fullName: string;
}

export interface ProfileInfoProps {
  children: ChildEntry[];
  childrenLoading: boolean;
  user: UserProfile;
}

export interface ProfileFormProps {
  loading: boolean;
  profileData: ProfileResponse | null;
  profileError: string | null;
  profileForm: Record<string, string>;
  profileSuccess: boolean;
  showProfileEdit: boolean;
  userRole: string;
  onDismissError: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onToggleEdit: (value: boolean) => void;
  onUpdateField: (key: string, value: string) => void;
}

export interface PasswordPolicyResult {
  key: string;
  passed: boolean | null;
}

export interface SecuritySettingsProps {
  confirmPassword: string;
  currentPassword: string;
  isPending: boolean;
  newPassword: string;
  passwordError: string | null;
  passwordSuccess: boolean;
  policyResults: PasswordPolicyResult[];
  showPasswordForm: boolean;
  onCancel: () => void;
  onChangeConfirmPassword: (value: string) => void;
  onChangeCurrentPassword: (value: string) => void;
  onChangeNewPassword: (value: string) => void;
  onDismissError: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onToggle: (value: boolean) => void;
}

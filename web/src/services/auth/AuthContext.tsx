/**
 * Authentication context and session management.
 *
 * Reference: S-076 — Session management
 * - Access token in React context (memory only)
 * - Refresh via HttpOnly cookie (auto on 401)
 * - CSRF double-submit cookie pattern
 * - Logout clears all state
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { api, setAccessToken, ApiClientError, type ApiError } from '@/services/api/client';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  school_id: string;
  totp_enabled?: boolean;
  permissions: string[];
  memberships: Array<{
    school_id: string;
    role: string;
    status: string;
  }>;
}

interface TwoFactorPending {
  tempToken: string;
  email: string;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  twoFactorPending: TwoFactorPending | null;
}

export interface AuthContextValue extends AuthState {
  login: (email: string, password: string, schoolId: string) => Promise<void>;
  verify2fa: (code: string) => Promise<void>;
  cancel2fa: () => void;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

interface AuthProviderProps {
  children: ReactNode;
}

function mapLoginErrorToTranslationKey(error?: Pick<ApiError, 'code' | 'message'> | null): string {
  const backendMsg = typeof error?.message === 'string' ? error.message : '';
  const errCode = typeof error?.code === 'string' ? error.code : '';
  const normalizedMessage = backendMsg.toLowerCase();

  if (errCode === 'ERR-IAM-401' || normalizedMessage.includes('invalid')) {
    return 'login.error.invalid';
  }

  if (
    errCode === 'ERR-IAM-403' ||
    normalizedMessage.includes('locked') ||
    normalizedMessage.includes('disabled')
  ) {
    return 'login.error.locked';
  }

  return 'login.error.generic';
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true, // start loading to check for existing session
    error: null,
    twoFactorPending: null,
  });

  // Try to restore session on mount (via refresh token cookie)
  useEffect(() => {
    let cancelled = false;

    async function tryRestore() {
      try {
        // Attempt silent refresh
        const csrf = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
        if (!csrf) {
          // No CSRF cookie = no refresh token = not logged in
          if (!cancelled) {
            setState((s) => ({ ...s, isLoading: false }));
          }
          return;
        }

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (csrf[1]) {
          headers['X-CSRF-Token'] = decodeURIComponent(csrf[1]);
        }

        const refreshResp = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers,
          credentials: 'include',
        });

        if (!refreshResp.ok) {
          if (!cancelled) {
            setState((s) => ({ ...s, isLoading: false }));
          }
          return;
        }

        const refreshBody = await refreshResp.json();
        const token = refreshBody.data?.access_token;
        if (!token) {
          if (!cancelled) setState((s) => ({ ...s, isLoading: false }));
          return;
        }

        setAccessToken(token);

        // Fetch user profile
        const profileResp = await api.get<UserProfile>('/auth/me');
        if (!cancelled) {
          setState({
            user: profileResp.data,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            twoFactorPending: null,
          });
        }
      } catch {
        if (!cancelled) {
          setAccessToken(null);
          setState((s) => ({ ...s, isLoading: false }));
        }
      }
    }

    tryRestore();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string, schoolId: string) => {
    setState((s) => ({ ...s, isLoading: true, error: null, twoFactorPending: null }));

    try {
      const loginResp = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password, school_id: schoolId }),
      });

      const loginBody = await loginResp.json();

      if (!loginResp.ok) {
        const errorKey = mapLoginErrorToTranslationKey(loginBody?.error);
        setState((s) => ({ ...s, isLoading: false, error: errorKey }));
        return;
      }

      // Handle 2FA required response
      if (loginBody.data?.requires_2fa) {
        setState((s) => ({
          ...s,
          isLoading: false,
          twoFactorPending: {
            tempToken: loginBody.data.temp_token,
            email,
          },
        }));
        return;
      }

      const token = loginBody.data?.access_token;
      if (!token) {
        setState((s) => ({ ...s, isLoading: false, error: 'login.error.generic' }));
        return;
      }

      setAccessToken(token);

      // Fetch profile
      const profileResp = await api.get<UserProfile>('/auth/me');
      setState({
        user: profileResp.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        twoFactorPending: null,
      });
    } catch (err) {
      const errorKey =
        err instanceof ApiClientError
          ? mapLoginErrorToTranslationKey(err.apiError)
          : 'login.error.generic';
      setState((s) => ({ ...s, isLoading: false, error: errorKey }));
    }
  }, []);

  const verify2fa = useCallback(
    async (code: string) => {
      if (!state.twoFactorPending) return;
      setState((s) => ({ ...s, isLoading: true, error: null }));

      try {
        const resp = await fetch('/api/v1/auth/2fa/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            temp_token: state.twoFactorPending.tempToken,
            code,
          }),
        });

        const body = await resp.json();

        if (!resp.ok) {
          const errMsg = body?.error?.message || 'Verification failed';
          setState((s) => ({ ...s, isLoading: false, error: errMsg }));
          return;
        }

        const token = body.data?.access_token;
        if (!token) {
          setState((s) => ({ ...s, isLoading: false, error: 'No access token received' }));
          return;
        }

        setAccessToken(token);

        const profileResp = await api.get<UserProfile>('/auth/me');
        setState({
          user: profileResp.data,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          twoFactorPending: null,
        });
      } catch (err) {
        const msg = err instanceof ApiClientError ? err.apiError.message : 'Verification failed';
        setState((s) => ({ ...s, isLoading: false, error: msg }));
      }
    },
    [state.twoFactorPending],
  );

  const cancel2fa = useCallback(() => {
    setState((s) => ({ ...s, twoFactorPending: null, error: null }));
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors
    } finally {
      setAccessToken(null);
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        twoFactorPending: null,
      });
    }
  }, []);

  const clearError = useCallback(() => {
    setState((s) => ({ ...s, error: null }));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      verify2fa,
      cancel2fa,
      logout,
      clearError,
    }),
    [state, login, verify2fa, cancel2fa, logout, clearError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

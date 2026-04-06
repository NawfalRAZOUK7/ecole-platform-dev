import type { PropsWithChildren, ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import i18n, { applyDirection } from '@/shared/i18n';
import { AuthContext, type AuthContextValue, type UserProfile } from '@/services/auth/AuthContext';
import { createUser } from './factories';

export interface RenderWithProvidersOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  user?: Partial<UserProfile> | null;
  queryClient?: QueryClient;
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

function createAuthValue(userOverride?: Partial<UserProfile> | null): AuthContextValue {
  const user = userOverride === null ? null : createUser(userOverride ?? {});
  return {
    user,
    isAuthenticated: Boolean(user),
    isLoading: false,
    error: null,
    twoFactorPending: null,
    login: async () => undefined,
    verify2fa: async () => undefined,
    cancel2fa: () => undefined,
    logout: async () => undefined,
    clearError: () => undefined,
  };
}

export function renderWithProviders(
  ui: ReactElement,
  { route = '/', user, queryClient, ...renderOptions }: RenderWithProvidersOptions = {}
) {
  const testQueryClient = queryClient ?? createQueryClient();
  const authValue = createAuthValue(user);

  void i18n.changeLanguage('en');
  applyDirection('en');

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={testQueryClient}>
          <AuthContext.Provider value={authValue}>
            <MemoryRouter initialEntries={[route]}>
              {children}
            </MemoryRouter>
          </AuthContext.Provider>
        </QueryClientProvider>
      </I18nextProvider>
    );
  }

  return {
    queryClient: testQueryClient,
    authValue,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

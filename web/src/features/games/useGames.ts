import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { gamesService, type GameConfigFilters, type GameConfigPayload } from './games.service';

export const gamesQueryKeys = {
  all: ['games'] as const,
  configs: (filters: Omit<GameConfigFilters, 'cursor'>) =>
    [...gamesQueryKeys.all, 'configs', filters] as const,
  config: (gameId: string | null) => [...gamesQueryKeys.all, 'config', gameId] as const,
};

export function useGameConfigs(filters: Omit<GameConfigFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: gamesQueryKeys.configs(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      gamesService.listConfigs({
        ...filters,
        cursor: pageParam,
        limit: 20,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useGameConfig(gameId: string | null | undefined, enabled: boolean) {
  return useQuery({
    queryKey: gamesQueryKeys.config(gameId || null),
    queryFn: async () => (await gamesService.getConfig(gameId!)).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateGameConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: GameConfigPayload) =>
      (await gamesService.createConfig(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: gamesQueryKeys.all });
    },
  });
}

export function useUpdateGameConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      gameId,
      payload,
    }: {
      gameId: string;
      payload: Partial<GameConfigPayload>;
    }) => (await gamesService.updateConfig(gameId, payload)).data,
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: gamesQueryKeys.all }),
        queryClient.invalidateQueries({
          queryKey: gamesQueryKeys.config(variables.gameId),
        }),
      ]);
    },
  });
}

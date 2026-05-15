import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { gamesService, type GameConfig, type ListGameConfigsFilters } from '../api/games.api';

export type GameConfigInput = Omit<GameConfig, 'id' | 'createdAt' | 'updatedAt'>;

export const gamesQueryKeys = {
  all: ['games'] as const,
  configs: (filters: Omit<ListGameConfigsFilters, 'cursor' | 'limit'>) =>
    [...gamesQueryKeys.all, 'configs', filters] as const,
  config: (gameId: string | null) => [...gamesQueryKeys.all, 'config', gameId] as const,
};

export function useGameConfigs(
  filters: Omit<ListGameConfigsFilters, 'cursor' | 'limit'>,
  pageSize = 12,
) {
  return useInfiniteQuery({
    queryKey: gamesQueryKeys.configs(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      gamesService.listConfigs({
        ...filters,
        cursor: pageParam,
        limit: pageSize,
      }),
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useGameConfig(gameId: string | null | undefined, enabled = Boolean(gameId)) {
  return useQuery({
    queryKey: gamesQueryKeys.config(gameId || null),
    queryFn: async () => gamesService.getConfig(gameId!),
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateGameConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: GameConfigInput) => gamesService.createConfig(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: gamesQueryKeys.all });
    },
  });
}

export function useUpdateGameConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ gameId, payload }: { gameId: string; payload: Partial<GameConfig> }) =>
      gamesService.updateConfig(gameId, payload),
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

export function useCompleteGameConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      gameId,
      score,
      timeSeconds,
    }: {
      gameId: string;
      score: number;
      timeSeconds: number;
    }) => gamesService.completeConfig(gameId, { score, timeSeconds }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['rewards'] });
    },
  });
}

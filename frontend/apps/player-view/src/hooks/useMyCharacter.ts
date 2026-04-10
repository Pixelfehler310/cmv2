import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CharacterCommandEnvelope, IHostBridge, apiClient } from "@rpg/bridge";
import { Character } from "../types";

type CharacterWritePayload = Record<string, unknown>;

type UpdateCharacterInput = {
  characterId: string;
  payload: CharacterWritePayload;
};

const myCharacterKey = (campaignId: string) => ["my-character", campaignId] as const;

const extractReason = (envelope: CharacterCommandEnvelope<unknown>): string => {
  return envelope.reason_code ?? "CHARACTER_COMMAND_DENIED";
};

const parseCharacters = (envelope: CharacterCommandEnvelope<Record<string, unknown>[]>) => {
  if (envelope.status !== "resolved") {
    throw new Error(extractReason(envelope));
  }
  return envelope.payload as unknown as Character[];
};

export const useMyCharacter = (bridge: IHostBridge, campaignId: string) => {
  return useQuery({
    queryKey: myCharacterKey(campaignId),
    queryFn: async (): Promise<Character | null> => {
      const user = await bridge.auth.getUser();
      if (!user || !campaignId) {
        return null;
      }

      const envelope = await apiClient.characters.list({
        campaign_id: campaignId,
        player_id: user.id,
      });
      const rows = parseCharacters(envelope);
      return rows[0] ?? null;
    },
    enabled: !!campaignId,
  });
};

export const useCreateCharacter = (campaignId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CharacterWritePayload) => {
      const envelope = await apiClient.characters.create(payload);
      if (envelope.status !== "resolved") {
        throw new Error(extractReason(envelope));
      }
      return envelope;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: myCharacterKey(campaignId) });
    },
  });
};

export const useUpdateCharacter = (campaignId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ characterId, payload }: UpdateCharacterInput) => {
      const envelope = await apiClient.characters.update(characterId, payload);
      if (envelope.status !== "resolved") {
        throw new Error(extractReason(envelope));
      }
      return envelope;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: myCharacterKey(campaignId) });
    },
  });
};

export const useCharacterSheet = (characterId: string | null, catalogRevision: number) => {
  return useQuery({
    queryKey: ["character-sheet", characterId, catalogRevision],
    queryFn: async () => {
      if (!characterId) {
        return null;
      }
      return apiClient.characters.getSheet(characterId, { catalog_revision: catalogRevision });
    },
    enabled: !!characterId && catalogRevision >= 0,
  });
};

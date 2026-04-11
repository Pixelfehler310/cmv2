import { useState } from "react";
import { useCreateCompendiumDefinition, useUpdateCompendiumDefinition } from "../../../hooks/useEntities";
import { extractValidationErrorMap } from "./validationErrorMap";

export function useEntityForm<T extends Record<string, any>>({ initialData, packId, family, onSave }: { initialData?: any; packId: string; family: string; onSave?: (data: any) => void }) {
  const isNew = !initialData?.id;
  const [formData, setFormData] = useState<T>(initialData || { name: "", slug: "" });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const createMutation = useCreateCompendiumDefinition();
  const updateMutation = useUpdateCompendiumDefinition();
  const mutation = isNew ? createMutation : updateMutation;

  const handleSave = async (extraPayload: any = {}) => {
    setFieldErrors({});
    const payload = {
      ...initialData,
      ...formData,
      ...extraPayload,
      family,
      pack_id: packId,
    };

    try {
      if (isNew) {
        const result = await createMutation.mutateAsync({ payload });
        if (onSave) onSave(result);
      } else {
        const result = await updateMutation.mutateAsync({
          definitionId: initialData?.id,
          updates: payload,
          expectedContentVersion: initialData?.content_version,
        });
        if (onSave) onSave(result);
      }
    } catch (error: any) {
      if (error && typeof error === "object") {
        const errors = extractValidationErrorMap(error);
        const flattenedErrors: Record<string, string> = {};
        Object.entries(errors).forEach(([key, values]) => {
          flattenedErrors[key] = values[0];
        });
        setFieldErrors(flattenedErrors);
      }
    }
  };

  return { formData, setFormData, fieldErrors, handleSave, isNew, mutation };
}

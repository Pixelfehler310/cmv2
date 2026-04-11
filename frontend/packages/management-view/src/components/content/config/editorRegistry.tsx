import React from "react";
import { MonsterEditor } from "./forms/MonsterEditor";
import { SpellEditor } from "./forms/SpellEditor";
import { ItemEditor } from "./forms/ItemEditor";
import { SpeciesEditor } from "./forms/SpeciesEditor";
import { ClassEditor } from "./forms/ClassEditor";
import { BackgroundEditor } from "./forms/BackgroundEditor";
import { LoreEditor } from "./forms/LoreEditor";
import { ConditionEditor } from "./forms/ConditionEditor";
import { FactionEditor } from "./forms/FactionEditor";
import { RegionEditor } from "./forms/RegionEditor";
import { PlaceEditor } from "./forms/PlaceEditor";

export const getEditorComponent = (family: string, props: any) => {
  switch (family) {
    case "monster":
      return <MonsterEditor {...props} />;
    case "spell":
      return <SpellEditor {...props} />;
    case "item":
      return <ItemEditor {...props} />;
    case "species":
      return <SpeciesEditor {...props} />;
    case "class":
      return <ClassEditor {...props} />;
    case "background":
      return <BackgroundEditor {...props} />;
    case "lore":
      return <LoreEditor {...props} />;
    case "condition":
      return <ConditionEditor {...props} />;
    case "faction":
      return <FactionEditor {...props} />;
    case "region":
      return <RegionEditor {...props} />;
    case "place":
      return <PlaceEditor {...props} />;
    default:
      return <div>Editor not found for family: {family}</div>;
  }
};

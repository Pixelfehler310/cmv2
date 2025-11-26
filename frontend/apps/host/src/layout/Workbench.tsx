import React from "react";
import { Layout, Model, TabNode } from "flexlayout-react";
import "flexlayout-react/style/light.css";
import { defaultLayout } from "./defaultLayout";

const factory = (node: TabNode) => {
  const component = node.getComponent();
  if (component === "dm-view") {
    return <div className="p-4 bg-slate-100 h-full">DM View Placeholder</div>;
  }
  if (component === "player-sheet") {
    return <div className="p-4 bg-slate-50 h-full">Player Sheet Placeholder</div>;
  }
  return <div className="p-4">Unknown Component</div>;
};

export const Workbench = () => {
  const model = Model.fromJson(defaultLayout);

  return (
    <div className="relative flex-1 h-full w-full">
      <Layout model={model} factory={factory} />
    </div>
  );
};

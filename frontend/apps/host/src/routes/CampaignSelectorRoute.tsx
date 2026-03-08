import { CampaignGrid } from "@rpg/management-view";

export const CampaignSelectorRoute = () => {
  return (
    <div className="h-full bg-background flex flex-col p-8">
      <div className="max-w-7xl mx-auto w-full">
        <CampaignGrid />
      </div>
    </div>
  );
};

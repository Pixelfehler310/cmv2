import { useParams } from "react-router-dom";
import { ContentManager } from "@rpg/management-view";

export const ContentRoute = () => {
  const { family } = useParams();

  return (
    <div className="h-full bg-background flex flex-col p-8">
      <div className="max-w-7xl mx-auto w-full h-full">
        <ContentManager initialFamily={family} />
      </div>
    </div>
  );
};

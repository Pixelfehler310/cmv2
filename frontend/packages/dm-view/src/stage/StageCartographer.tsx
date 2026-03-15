import React from "react";

export interface StageCartographerProps {
  tokens: any[];
  mapUrl?: string;
}

export const StageCartographer: React.FC<StageCartographerProps> = ({
  tokens,
  mapUrl,
}) => {
  return (
    <div
      className="w-full h-full relative bg-gray-900 border border-gray-800"
      style={{
        backgroundImage: mapUrl ? `url(${mapUrl})` : "none",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {tokens.map((token) => (
        <div
          key={token.id}
          className={`absolute flex items-center justify-center w-12 h-12 rounded-full border-4 ${token.healthRingColor || "border-gray-500"} shadow-lg transition-all duration-300`}
          style={{
            left: `${token.x || 0}px`,
            top: `${token.y || 0}px`,
            backgroundColor: token.healthStatus === "Dead" ? "#333" : "#4f46e5",
          }}
          title={token.name}
        >
          <span className="text-xs text-white uppercase font-bold truncate px-1 drop-shadow-md">
            {token.name?.substring(0, 3)}
          </span>
        </div>
      ))}
    </div>
  );
};

import { ReactNode } from "react";

export const StageLayout = ({ children }: { children: ReactNode }) => {
  return (
    <div className="absolute inset-0 bg-black overflow-hidden flex flex-col">
      {/* 
        This is a chromeless layout. 
        It only renders its children which will be the map canvas and overlays.
      */}
      {children}
    </div>
  );
};

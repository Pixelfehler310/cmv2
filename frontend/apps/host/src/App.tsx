import React from "react";
import { Workbench } from "./layout/Workbench";

function App() {
  return (
    <div className="h-screen w-screen flex flex-col">
      <header className="h-12 border-b flex items-center px-4 bg-background">
        <h1 className="font-bold text-lg">Open RPG Engine</h1>
      </header>
      <main className="flex-1 relative overflow-hidden">
        <Workbench />
      </main>
    </div>
  );
}

export default App;

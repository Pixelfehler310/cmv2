
export const ChatPanel = () => {
  return (
    <div className="h-full flex flex-col bg-white/90">
      <div className="flex-1 p-4 overflow-y-auto space-y-2">
        <div className="text-sm"><span className="font-bold text-blue-600">DM:</span> Welcome to the game!</div>
        <div className="text-sm"><span className="font-bold text-slate-600">System:</span> Aragorn joined.</div>
      </div>
      <div className="p-2 border-t">
        <input type="text" placeholder="Type a message..." className="w-full px-2 py-1 border rounded" />
      </div>
    </div>
  );
};

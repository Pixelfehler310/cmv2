export const ChatPanel = () => {
  return (
    <div className="h-full flex flex-col bg-card text-card-foreground">
      <div className="flex-1 p-4 overflow-y-auto space-y-2">
        <div className="text-sm">
          <span className="font-bold text-primary">DM:</span> Welcome to the game!
        </div>
        <div className="text-sm">
          <span className="font-bold text-muted-foreground">System:</span> Aragorn joined.
        </div>
      </div>
      <div className="p-2 border-t border-border">
        <input
          type="text"
          placeholder="Type a message..."
          className="w-full px-3 py-2 bg-input rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>
    </div>
  );
};

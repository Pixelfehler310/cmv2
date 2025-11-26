import * as React from "react";
import { cn } from "../../lib/utils";

export interface ChatMessage {
  id: string;
  timestamp: Date;
  type: 'dice' | 'action' | 'system' | 'chat';
  content: string;
  metadata?: Record<string, any>;
}

export interface ChatLogProps {
  messages: ChatMessage[];
  className?: string;
  maxMessages?: number;
}

export function ChatLog({ messages, className, maxMessages = 100 }: ChatLogProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const displayedMessages = messages.slice(-maxMessages);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getMessageColor = (type: ChatMessage['type']) => {
    switch (type) {
      case 'dice':
        return 'text-blue-600';
      case 'action':
        return 'text-green-600';
      case 'system':
        return 'text-yellow-600';
      default:
        return 'text-foreground';
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-muted/30 rounded">
        {displayedMessages.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center">No messages yet</p>
        ) : (
          displayedMessages.map((message) => (
            <div key={message.id} className="text-sm">
              <span className="text-muted-foreground text-xs">
                [{formatTimestamp(message.timestamp)}]
              </span>{' '}
              <span className={cn("font-medium", getMessageColor(message.type))}>
                [{message.type.toUpperCase()}]
              </span>{' '}
              <span>{message.content}</span>
              {message.metadata && Object.keys(message.metadata).length > 0 && (
                <div className="ml-8 text-xs text-muted-foreground">
                  {JSON.stringify(message.metadata, null, 2)}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}


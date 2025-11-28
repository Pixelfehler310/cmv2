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
export declare function ChatLog({ messages, className, maxMessages }: ChatLogProps): import("react/jsx-runtime").JSX.Element;
//# sourceMappingURL=ChatLog.d.ts.map
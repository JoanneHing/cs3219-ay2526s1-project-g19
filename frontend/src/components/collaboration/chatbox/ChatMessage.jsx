import { Bot, User } from "lucide-react";

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const ChatMessage = ({ msg, isCurrentUser }) => (
  <div className={`flex gap-3 ${isCurrentUser ? 'justify-end' : 'justify-start'}`}>
    {!isCurrentUser && (
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary-light flex items-center justify-center flex-shrink-0 shadow-md">
        <Bot className="w-4 h-4 text-white" />
      </div>
    )}
    <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'} max-w-[75%]`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-gray-400">
          {msg.username}
        </span>
        <span className="text-xs text-gray-500">
          {formatTimestamp(msg.__createdtime__)}
        </span>
      </div>
      <div
        className={`px-4 py-2.5 rounded-2xl shadow-sm ${
          isCurrentUser
            ? 'bg-gradient-to-r from-primary-light to-primary text-white rounded-tr-sm'
            : 'bg-background border border-gray-700 text-gray-200 rounded-tl-sm'
        }`}
      >
        <p className="text-sm leading-relaxed break-words">
          {msg.message}
        </p>
      </div>
    </div>
    {isCurrentUser && (
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-light to-primary flex items-center justify-center flex-shrink-0 shadow-md">
        <User className="w-4 h-4 text-white" />
      </div>
    )}
  </div>
);

export default ChatMessage;
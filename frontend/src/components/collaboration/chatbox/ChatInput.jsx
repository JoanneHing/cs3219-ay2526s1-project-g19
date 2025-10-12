import { Send } from "lucide-react";

const ChatInput = ({ message, setMessage, handleSubmit }) => (
  <div className="border-t border-gray-700 bg-background p-2 flex-shrink-0">
    <form className="flex gap-2" onSubmit={handleSubmit}>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
        placeholder="Type a message..."
        className="flex-1 px-3 py-2 text-sm bg-background-secondary border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-gray-200 placeholder-gray-400 transition-all"
      />
      <button
        type="submit"
        className="px-4 py-2 bg-gradient-to-r from-primary to-blue-800 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2 font-medium active:scale-95 flex-shrink-0"
      >
        <Send className="w-4 h-4" />
      </button>
    </form>
  </div>
);

export default ChatInput;
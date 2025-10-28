import { RefreshCw, ArrowRight } from 'lucide-react';

const SessionStatusCard = ({ isChecking, activeSession, onReconnect, onStartNew }) => {
  const formatStartTime = (startedAt) => {
    if (!startedAt) return 'N/A';
    
    const date = typeof startedAt === 'string' 
      ? new Date(startedAt + 'Z')
      : new Date(startedAt);
    
    return date.toLocaleString();
  };

  if (isChecking) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-300">Checking for active sessions...</p>
        </div>
      </div>
    );
  }

  if (activeSession) {
    return (
      <div className="bg-gradient-to-r from-blue-900/50 to-indigo-900/50 border-2 border-blue-500 rounded-lg p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <h2 className="text-xl font-bold text-white">Active Session Found</h2>
        </div>
        
        <div className="space-y-2 text-gray-300 mb-6">
          <p><span className="font-semibold">Session ID:</span> {activeSession.id}</p>
          <p><span className="font-semibold">Language:</span> {activeSession.language || 'N/A'}</p>
          <p><span className="font-semibold">Started:</span> {formatStartTime(activeSession.started_at)}</p>
          {activeSession.title && (
            <p>
              <span className="font-semibold">Question:</span>{' '}
              <span className="text-blue-300">{activeSession.title}</span>
            </p>
          )}
        </div>

        <button
          onClick={onReconnect}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-lg"
        >
          <RefreshCw className="w-5 h-5" />
          Reconnect to Session
        </button>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
      <p className="text-gray-300 mb-6">No active session found. Start a new session below!</p>
      
      <button
        onClick={onStartNew}
        className="w-full flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold text-lg rounded-lg transition-all shadow-xl"
      >
        Start New Session
        <ArrowRight className="w-5 h-5" />
      </button>
    </div>
  );
};

export default SessionStatusCard;
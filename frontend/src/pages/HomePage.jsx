import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { sessionService } from '../api/services/sessionService';
import SessionStatusCard from '../components/home/SessionStatusCard';

const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeSession, setActiveSession] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    const checkActiveSession = async () => {
      if (!user?.id) {
        setIsCheckingSession(false);
        return;
      }

      try {
        const sessionData = await sessionService.getActiveSession(user.id);
        
        if (sessionData && sessionData.id && !sessionData.ended_at) {
          setActiveSession({
            ...sessionData,
            session_id: sessionData.id
          });
        }
      } catch (error) {
        console.error('Failed to check active session:', error);
      } finally {
        setIsCheckingSession(false);
      }
    };

    checkActiveSession();
  }, [user?.id]);

  const handleReconnect = () => {
    if (activeSession) {
      navigate(`/collaboration/${activeSession.id}`, {
        state: { sessionData: activeSession }
      });
    }
  };

  const handleStartNewSession = () => {
    navigate('/matching');
  };

  return (
    <div className="w-full min-h-screen p-8 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-950 dark:via-slate-900 dark:to-indigo-950">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-4 text-white">Welcome to PeerPrep!</h1>
          <p className="text-lg text-gray-300">Your one-stop platform for peer-to-peer coding practice.</p>
        </div>

        <SessionStatusCard
          isChecking={isCheckingSession}
          activeSession={activeSession}
          onReconnect={handleReconnect}
          onStartNew={handleStartNewSession}
        />
      </div>
    </div>
  );
};

export default HomePage;

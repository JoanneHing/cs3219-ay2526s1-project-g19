import { AlertTriangle, Clock } from 'lucide-react';

const SessionTimerWarning = ({ timeRemaining, onContinue, isMaxTimeReached }) => {
    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (isMaxTimeReached) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
                <div className="rounded-lg shadow-lg p-8 max-w-xl w-full relative bg-background-secondary border border-gray-700">
                    <div className="text-center">
                        <div className="mx-auto w-16 h-16 flex items-center justify-center mb-4">
                            <AlertTriangle className="w-10 h-10 text-red-500" />
                        </div>
                        <h3 className="text-gray-200 font-bold text-2xl mb-2">
                            Session Time Limit Reached
                        </h3>
                        <p className="text-gray-400 p-2 mb-6">
                            The collaboration session has reached the maximum allowed time of 1 hour.
                            <br />
                            The session will be terminated automatically.
                        </p>

                        <div className="flex justify-center">
                            <button
                                onClick={onContinue}
                                className="w-1/2 text-lg font-bold py-3 rounded-lg border-2 bg-red-500 hover:bg-red-600">
                                Leave Session
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
            <div className="rounded-lg shadow-lg p-8 max-w-xl w-full relative bg-background-secondary border border-gray-700">
                <div className="text-center">
                    <div className="mx-auto w-16 h-16 flex items-center justify-center mb-4">
                        <Clock className="w-10 h-10 text-yellow-400" />
                    </div>
                    <h3 className="text-gray-200 font-bold text-2xl mb-2">
                        Session Time Ending Soon
                    </h3>
                    <p className="text-gray-400 p-2 mb-4">
                        Your collaboration session is about to reach the time limit.
                    </p>
                    <div className="border border-gray-700 rounded-lg p-4 mb-6">
                        <div className="text-gray-200 font-mono text-4xl font-bold mb-2">
                            {formatTime(timeRemaining)}
                        </div>
                        <div className="text-gray-400 text-sm">
                            remaining until session ends
                        </div>
                    </div>

                    <div className="flex justify-center">
                        <button
                            onClick={onContinue}
                            className="w-1/2 text-lg font-bold py-3 rounded-lg border-2 bg-primary hover:bg-primary-dark text-white">
                            Continue Session
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SessionTimerWarning;

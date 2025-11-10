import { useState, useEffect } from 'react';
import { Clock, Calendar, User, BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';
import { sessionService } from '../../api/services/sessionService';
import { useNotification } from '../../contexts/NotificationContext';
import { userService } from '../../api/services/userService';

const SESSIONS_PER_PAGE = 5;

const SessionHistory = () => {
    const [sessions, setSessions] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [isLoading, setIsLoading] = useState(true);
    const [hasMore, setHasMore] = useState(true);
    const [partnerNames, setPartnerNames] = useState({}); // Store partner names by user ID
    const { showError } = useNotification();

    useEffect(() => {
        fetchSessionHistory(currentPage);
    }, [currentPage]);

    const fetchSessionHistory = async (page) => {
        setIsLoading(true);
        try {
            const response = await sessionService.getHistory(page, SESSIONS_PER_PAGE);
            const data = response.data;
            
            // If we get an empty array, disable next 
            // If we get less than the page size, there are no more pages
            // Only enable next if we got exactly the page size AND it's not empty
            if (data.length === 0 && page > 1) {
                // Empty page after page 1 means we went too far, go back
                setCurrentPage(page - 1);
                setHasMore(false);
                return;
            }
            
            setHasMore(data.length === SESSIONS_PER_PAGE);
            setSessions(data);
            
            // Fetch partner names for all sessions
            const uniquePartnerIds = [...new Set(data.map(session => session.matched_user_id))];
            const names = {};
            
            await Promise.all(
                uniquePartnerIds.map(async (partnerId) => {
                    // Skip if we already have this partner's name
                    if (partnerNames[partnerId]) {
                        names[partnerId] = partnerNames[partnerId];
                        return;
                    }
                    
                    try {
                        const profileResponse = await userService.getPublicProfile(partnerId);
                        names[partnerId] = profileResponse.data?.user?.display_name || 'Unknown User';
                    } catch (error) {
                        console.error(`Failed to fetch partner name for ${partnerId}:`, error);
                        names[partnerId] = 'Unknown User';
                    }
                })
            );
            
            setPartnerNames(prev => ({ ...prev, ...names }));
        } catch (error) {
            console.error('Error fetching session history:', error);
            showError('Error', 'Failed to load session history');
            setSessions([]);
            setHasMore(false);
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    };

    const calculateDuration = (startedAt, endedAt) => {
        if (!endedAt) return 'In Progress';
        
        const start = new Date(startedAt);
        const end = new Date(endedAt);
        const durationMs = end - start;
        
        const hours = Math.floor(durationMs / (1000 * 60 * 60));
        const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    };

    const getDifficultyColor = (difficulty) => {
        switch (difficulty.toLowerCase()) {
            case 'easy':
                return 'text-green-400 bg-green-900/20 border-green-700';
            case 'medium':
                return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
            case 'hard':
                return 'text-red-400 bg-red-900/20 border-red-700';
            default:
                return 'text-gray-400 bg-gray-900/20 border-gray-700';
        }
    };

    const handlePreviousPage = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
        }
    };

    const handleNextPage = () => {
        if (hasMore) {
            setCurrentPage(currentPage + 1);
        }
    };

    if (isLoading && sessions.length === 0) {
        return (
            <div className="mt-8">
                <h2 className="text-2xl font-bold mb-4">Past Sessions</h2>
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="ml-3 text-gray-400">Loading sessions...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="mt-8">
            <h2 className="text-2xl font-bold mb-4">Past Sessions</h2>
            
            {sessions.length === 0 ? (
                <div className="bg-background-secondary border border-gray-700 rounded-lg p-8 text-center">
                    <BookOpen className="mx-auto h-12 w-12 text-gray-500 mb-3" />
                    <p className="text-gray-400">No past sessions yet</p>
                    <p className="text-gray-500 text-sm mt-2">Start collaborating to build your session history!</p>
                </div>
            ) : (
                <>
                    <div className="space-y-4">
                        {sessions.map((session) => (
                            <div 
                                key={session.id}
                                className="bg-background-secondary border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors"
                            >
                                {/* Header with Question Title and Difficulty */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-semibold text-gray-200 mb-2">
                                            {session.question_title}
                                        </h3>
                                        <div className="flex flex-wrap gap-2 items-center">
                                            <span className={`px-2 py-1 text-xs font-medium rounded border ${getDifficultyColor(session.difficulty)}`}>
                                                {session.difficulty}
                                            </span>
                                            <span className="text-xs text-gray-400">
                                                Language: <span className="text-gray-300 font-medium">{session.language}</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Topics */}
                                {session.topics && session.topics.length > 0 && (
                                    <div className="mb-3">
                                        <div className="flex flex-wrap gap-2">
                                            {session.topics.map((topic, index) => (
                                                <span 
                                                    key={index}
                                                    className="px-2 py-1 text-xs bg-blue-900/20 text-blue-400 rounded border border-blue-800"
                                                >
                                                    {topic}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Company Tags */}
                                {session.company_tags && session.company_tags.length > 0 && (
                                    <div className="mb-3">
                                        <div className="flex flex-wrap gap-2">
                                            {session.company_tags.map((company, index) => (
                                                <span 
                                                    key={index}
                                                    className="px-2 py-1 text-xs bg-purple-900/20 text-purple-400 rounded border border-purple-800"
                                                >
                                                    {company}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Session Details */}
                                <div className="flex flex-wrap gap-4 text-sm text-gray-400 pt-3 border-t border-gray-700">
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4" />
                                        <span>{formatDate(session.started_at)}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4" />
                                        <span>{formatTime(session.started_at)} - {session.ended_at ? formatTime(session.ended_at) : 'Ongoing'}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4" />
                                        <span>Duration: {calculateDuration(session.started_at, session.ended_at)}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <User className="w-4 h-4" />
                                        <span>Partner: {partnerNames[session.matched_user_id] || 'Loading...'}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination Controls */}
                    <div className="flex items-center justify-between mt-6">
                        <button
                            onClick={handlePreviousPage}
                            disabled={currentPage === 1 || isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-background-secondary border border-gray-700 rounded-lg text-gray-300 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronLeft className="w-4 h-4" />
                            Previous
                        </button>

                        <span className="text-gray-400">
                            Page {currentPage}
                        </span>

                        <button
                            onClick={handleNextPage}
                            disabled={!hasMore || isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-background-secondary border border-gray-700 rounded-lg text-gray-300 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default SessionHistory;

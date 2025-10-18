import { UserCircle2, Loader2 } from "lucide-react";

const DIFFICULTIES_COLORS = {
    "e": "text-green-500 border-green-500",
    "m": "text-yellow-500 border-yellow-500",
    "h": "text-red-500 border-red-500"
};

const getDifficultyColor = (difficulty) => {
    return DIFFICULTIES_COLORS[difficulty] || "text-gray-500 border-gray-500";
}

const getDifficulties = (difficultyStr) => {
    switch (difficultyStr) {
        case "e":
            return "Easy";
        case "m":
            return "Medium";
        case "h":
            return "Hard";
        default:
            return "";
    }
}

/**
 * Match Found window to show matched user and matched selections
 * @param {string} user - The current user's name
 * @param {string} partner - The matched partner's name
 * @param {object} matchedSelections - The matched selections (topic, difficulty, language)
 * @param {function} onQuit - Function to call when user quits the match
 */
const MatchFound = ({ user1, user2, matchedSelections, onQuit}) => {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
            <div className = "rounded-lg shadow-lg p-8 max-w-lg w-full relative bg-background-secondary border border-gray-700">
                <div className="text-center">
                    <h3 className="text-gray-200 font-bold mb-6">Match Found!</h3>

                    <div className="flex justify-center items-center mb-4 font-semibold text-lg text-gray-300 gap-2 grid grid-cols-3">
                        <div className="flex flex-col items-center">
                            <UserCircle2 className="h-20 w-20 text-primary mb-2"/>
                            <p className="text-lg font-bold">{user1}</p> {/* TODO: replace with actual user name */}                            
                        </div>

                        <span className="text-4xl text-gray-400 font-extrabold"> VS </span>

                        <div className="flex flex-col items-center">
                            <UserCircle2 className="h-20 w-20 text-primary mb-2"/>
                            <p className="text-lg font-bold">{user2}</p> {/* TODO: replace with actual partner name */}
                        </div>
                    </div>

                    <div className="flex justify-around text-sm font-semibold mt-5 mb-8">
                        <span className="px-3 py-1 rounded-full text-green-500 bg-bg-secondary border border-green-500">
                            Topic: {matchedSelections.topic}
                        </span>
                        <span className={`px-3 py-1 rounded-full bg-bg-secondary border ${getDifficultyColor(matchedSelections.difficulty)}`}>
                            Difficulty: {getDifficulties(matchedSelections.difficulty)}
                        </span>
                        <span className="px-3 py-1 rounded-full text-green-500 bg-bg-secondary border border-green-500">
                            Language: {matchedSelections.language}
                        </span>
                    </div>

                    <p>
                        <Loader2 className="inline-block animate-spin mr-2" />
                        Please wait while we create the collaboration space...
                    </p>

                    <button
                        onClick={onQuit}
                        className="mt-8 w-full text-lg font-bold py-3 rounded-lg border-2 bg-red-500 hover:bg-red-600">
                        Quit Match
                    </button>
                </div>
            </div>
        </div>
    );
}

export default MatchFound;
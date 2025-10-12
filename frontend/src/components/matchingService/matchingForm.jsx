import { Children, useState } from "react";
import { ChevronDown } from "lucide-react";

// Selection Options
// Hardcoded for now (If backend support is added, fetch from backend)
// Topics are form leetcode 150
const TOPICS = [
    "Array",
    "String",
    "Two Pointers",
    "Sliding Window",
    "Matrix",
    "Hashmap",
    "Intervals",
    "Stack",
    "Linked List",
    "Binary Tree General",
    "Binary Tree BFS",
    "Binary Search Tree",
    "Graph General",
    "Graph BFS",
    "Trie",
    "Backtracking",
    "Divide and Conquer",
    "Kadane's Algorithm",
    "Binary Search",
    "Heap",
    "Bit Manipulation",
    "Math",
    "1D DP",
    "Multi-D DP"
];

// This list is used to check if all difficulties are selected
// Then will automatically select "Any"
const DIFFICULTIES = [
    "Easy",
    "Medium",
    "Hard"
];

// This is for rendering
const ALL_DIFFICULTIES = [...DIFFICULTIES, "Any"];

const LANGUAGES = [
    "Java",
    "Python",
    "C++",
    "C#",
    "JavaScript",
    "TypeScript",
    "Go",
    "Ruby",
    "Rust"
];

// Helper functions
const BubbleLabels = ({ label, isSelected, onClick}) => {
    const baseClass = "px-3 py-1 rounded-full border cursor-pointer select-none font-ubuntu text-sm transition duration-200";
    const selectedClass = "bg-primary text-gray-100 border-primary hover:bg-primary-dark hover:border-primary-dark";
    const unselectedClass = "bg-gray-700 text-gray-200 border border-gray-600 hover:text-white hover:bg-primary";

    return (
        <span
            onClick={onClick}
            className={`${baseClass} ${isSelected ? selectedClass : unselectedClass}`}
        >
            {label}
        </span>
    );
};

// Overylay for pop up windows
const Overlay = ({ Children }) => {
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
        <div className = "rounded-lg shadow-lg p-8 max-w-lg w-full relative bg-background-secondary border border-gray-700">
            {Children}
        </div>
    </div>
};

const MatchingForm = () => {
    const [selections, setSelections] = useState({
        topics: [],
        difficulties: [],
        preferredLanguage: '',
        backupLanguages: []
    });

    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    // Handlers for selections
    // For bubble selections: topics, backupLanguages
    const handleBubbleToggle = (field, item) => {
        setSelections(prev => {
            const currentSelections = prev[field];
            const isSelected = currentSelections.includes(item);

            let updatedSelections;

            if (isSelected) {
                updatedSelections = currentSelections.filter(i => i !== item);
            } else {
                // Enforced max 2 selections for backupLanguages
                if (field === 'backupLanguages' && currentSelections.length >= 2) {
                    return prev; // Do nothing if already 2 selected
                } else {
                    updatedSelections = [...currentSelections, item];
                }
            }

            return {...prev, [field]: updatedSelections};
        });
    }

    // For difficulty selection
    const handleDifficultyToggle = (difficulty) => {
        setSelections(prev => {
            let currentDifficulties = [...prev.difficulties];
            const isSelected = currentDifficulties.includes(difficulty);
            let updatedDifficulties;

            if (difficulty === "Any") {
                updatedDifficulties = isSelected ? [] : ["Any"];
            } else {
                let tempDiffoculties;

                if (isSelected) {
                    // Remove difficulty, and if "Any" is selected, remove also
                    tempDiffoculties = currentDifficulties.filter(d => d !== difficulty && d !== "Any");
                } else {
                    // Add difficulty, remove "Any" if it was selected
                    tempDiffoculties = [...currentDifficulties.filter(d => d !== "Any"), difficulty];
                }

                // Check if all difficulties are selected
                if (tempDiffoculties.length === DIFFICULTIES.length) {
                    updatedDifficulties = ["Any"];
                } else {
                    updatedDifficulties = tempDiffoculties;
                }
            }

            return {...prev, difficulties: updatedDifficulties};
        });
    }

    const isAnySelected = selections.difficulties.includes("Any") && selections.difficulties.length === 1;

    // Handler for preferred language dropdown
    const handlePreferredLanguageSelect = (language) => {
        setSelections(prev => ({...prev, preferredLanguage: language}));
        setIsDropdownOpen(false);
    }

    const renderLanguageDropdown = LANGUAGES.map(lang => (
        <div
            key={lang}
            className={"px-4 py-2 hover:bg-gray-900 cursor-pointer text-gray-200"}
            onClick={() => handlePreferredLanguageSelect(lang)}
        >
            {lang}
        </div>
    ));

    // Form submission handler
    const handleSubmit = (e) => {
        e.preventDefault();

        // Connect with api here
        console.log(`Matching selections:
            Topics: ${selections.topics.join(", ") || "Any"}
            Difficulties: ${selections.difficulties.join(", ") || "Any"}
            Preferred Language: ${selections.preferredLanguage || "None"}
            Backup Languages: ${selections.backupLanguages.join(", ") || "None"}
        `);

    }

    return (
            <div className="bg-background-secondary p-6 rounded-xl w-full max-w-6xl shadow-2xl border border-gray-700">
                {/* Form Header */}
                <div className="mb-4 border-b border-gray-700 pb-4">
                    <h3 className="text-white font-bold">
                        Find a match
                    </h3>
                    <p className="text-gray-400 text-s pt-3">
                        System will find a match based on your selected topics, difficulty and programming language.
                    </p>
                </div>

                {/* Topic Selection */}
                <section className="mb-8">
                    <h4 className ="text-white font-semibold mb-3">
                        Topics: <span className="text-sm font-normal text-gray-400 pl-1">Select one or more, default is set as Any</span>
                    </h4>
                    <div className="flex flex-wrap gap-3 border border-gray-600 p-4 rounded-lg max-h-48 overflow-y-auto justify-start">
                        {TOPICS.map(topic => (
                            <BubbleLabels
                                key={topic}
                                label={topic}
                                isSelected={selections.topics.includes(topic)}
                                onClick={() => handleBubbleToggle('topics', topic)}
                            />
                        ))}
                    </div>
                </section>

                {/* Difficulty Selection */}
                <section className="mb-8">
                    <h4 className ="text-white font-semibold mb-3">
                        Difficulty: <span className="text-sm font-normal text-gray-400 pl-1">Select one or more</span>
                    </h4>
                    {DIFFICULTIES.map(difficulty => (
                        <label key={difficulty} className="inline-flex items-center mr-6 mb-2 cursor-pointer">
                            <input
                                type="checkbox"
                                name="difficulty"
                                value={difficulty}
                                checked={selections.difficulties.includes(difficulty) || isAnySelected}
                                onChange={() => handleDifficultyToggle(difficulty)}
                                disabled={isAnySelected && difficulty !== "Any"}
                                className="form-checkbox h-5 w-5 text-primary bg-gray-700 border-gray-600 rounded focus:ring-0 cursor-pointer"
                            />
                            <span className="ml-2 text-gray-200 select-none">{difficulty}</span>
                        </label>
                    ))}
                    <label className="inline-flex items-center mr-6 mb-2 cursor-pointer">
                        <input
                            type="checkbox"
                            name="difficulty"
                            value="Any"
                            checked={isAnySelected}
                            onChange={() => handleDifficultyToggle("Any")}
                            className="form-checkbox h-5 w-5 text-secondary bg-gray-700 border-gray-600 rounded focus:ring-0 cursor-pointer"
                        />
                        <span className="ml-2 text-gray-200 select-none">Any</span>
                    </label>
                </section>

                {/* Preferred Language Selection */}
                <section className="grid mb-8 md:grid-cols-2 gap-8 mb-5">
                    <div>
                        <h4 className="text-white font-semibold mb-3">
                            Preferred Language: <span className="text-sm font-normal text-gray-400 pl-1">Select one</span>
                        </h4>
                        <div className="relative">
                            <button
                                type="button"
                                className="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-lg px-4 py-2 flex justify-between items-center focus:outline-none focus:ring-2 focus:ring-primary"
                                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                            >
                                <span className="text-gray-200">
                                    {selections.preferredLanguage || "Select one language"}
                                </span>
                                <ChevronDown className="ml-2 h-4 w-4 text-gray-400" />
                            </button>
                            {isDropdownOpen && (
                                <div className="absolute z-10 mt-1 w-full bg-background-secondary border border-gray-600 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                                    {renderLanguageDropdown}
                                </div>
                            )}
                        </div>
                    </div>
                    <div>
                        <h4 className="text-white font-semibold mb-3">
                            Backup Languages : <span className="text-sm font-normal text-gray-400 pl-1">Select up to two (Optional)</span>
                        </h4>
                        <div className="flex flex-wrap gap-3 border border-gray-600 p-4 rounded-lg max-h-48 overflow-y-auto justify-start">
                            {LANGUAGES.map(lang => (
                                <BubbleLabels
                                    key={lang}
                                    label={lang}
                                    isSelected={selections.backupLanguages.includes(lang)}
                                    onClick={() => handleBubbleToggle('backupLanguages', lang)}
                                />
                            ))}
                        </div>
                        <p className="text-sm text-gray-400 mt-2">
                            Enabled after 30s if no match found
                        </p>
                    </div>
                </section>

                {/* Submit Button */}
                <div className="text-center flex justify-center p-4">
                    <button
                        type="submit"
                        onClick={handleSubmit}
                        className="bg-primary hover:bg-primary-dark text-white font-semibold py-2 px-6 rounded-lg transition duration-200 w-full"
                    >
                        Find Match
                    </button>
                </div>
            </div>
    );
}

export default MatchingForm;
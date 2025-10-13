const EditorHeader = ({ 
  filename, 
  languages = [], 
  selectedLanguage, 
  onLanguageChange 
}) => (
  <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-4 py-2 flex items-center justify-between border-b border-slate-600">
    <div className="flex items-center gap-2">
      <div className="flex gap-1.5">
        <div className="w-3 h-3 rounded-full bg-red-500"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
        <div className="w-3 h-3 rounded-full bg-green-500"></div>
      </div>
      <span className="ml-2 text-slate-300 text-sm font-medium">{filename}</span>
    </div>
    
    {languages.length > 0 && (
      <div className="flex items-center gap-3">
        <label htmlFor="language-select" className="text-sm font-medium text-slate-400">
          Language:
        </label>
        <select
          id="language-select"
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-slate-500 transition-colors cursor-pointer"
        >
          {languages.map((lang) => (
            <option key={lang.id} value={lang.id} className="bg-slate-800">
              {lang.name}
            </option>
          ))}
        </select>
      </div>
    )}
  </div>
);

export default EditorHeader;
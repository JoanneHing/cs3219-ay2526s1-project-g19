import QuestionHeader from "./questionpanel/QuestionHeader";
import QuestionDescription from "./questionpanel/QuestionDescription";

export default function QuestionPanel() {
  // Updated dummy data based on API response structure
  const question = {
    title: "Reverse String",
    difficulty: "easy",
    topics: ["Array", "Two Pointers", "String"],
    statement_md: `Write a function that reverses a string. The input string is given as an array of characters s.

You must do this by modifying the input array in-place with O(1) extra memory.`,
    examples: [
      {
        input: 's = ["h","e","l","l","o"]',
        output: '["o","l","l","e","h"]',
        explanation: "The string is reversed in-place."
      },
      {
        input: 's = ["H","a","n","n","a","h"]',
        output: '["h","a","n","n","a","H"]',
        explanation: "The palindrome is reversed in-place."
      }
    ],
    constraints: [
      "1 ≤ s.length ≤ 10⁵",
      "s[i] is a printable ascii character"
    ],
    assets: "No additional assets required",
    company_tags: "Amazon, Google, Microsoft",
    stats: {
      views: 125430,
      attempts: 89234,
      solved: 78901,
      percentage_solved: 88.4,
      last_activity_at: "2025-10-10T13:57:48.968Z"
    }
  };

  return (
      <div className="bg-primary-secondary/80 backdrop-blur-xl">
        <QuestionHeader
          title={question.title}
          difficulty={question.difficulty}
          topics={question.topics}
          stats={question.stats}
          company_tags={question.company_tags}
        />
        <QuestionDescription
          statement={question.statement_md}
          examples={question.examples}
          constraints={question.constraints}
        />
      </div>
  );
}
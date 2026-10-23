/**
 * Password Strength Evaluator (Client-Side Only)
 * 
 * Strict Privacy Guarantee:
 * - Runs 100% locally in the user's browser.
 * - Zero network requests, zero logging, zero telemetry.
 * - Zero storage (passwords are never saved to localStorage, sessionStorage, or cookies).
 */

export interface CriteriaItem {
  id: string;
  name: string;
  met: boolean;
  score: number; // 0 to 100
  detail: string;
  category: "length" | "uppercase" | "lowercase" | "numbers" | "symbols" | "entropy";
}

export interface CharacterCounts {
  lowercase: number;
  uppercase: number;
  numbers: number;
  symbols: number;
}

export interface PasswordFeedback {
  score: number; // 0 to 4
  scorePercent: number; // 0 to 100%
  tier: "Very Weak" | "Weak" | "Moderate" | "Strong" | "Very Strong";
  colorClass: string;
  accentColor: string;
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
  length: number;
  counts: CharacterCounts;
  criteria: CriteriaItem[];
  warnings: string[];
  suggestions: string[];
  entropyBits: number;
  timeToCrack: string;
}

const COMMON_PATTERNS = [
  "password", "123456", "12345678", "qwerty", "admin", "welcome", "login",
  "iloveyou", "pakistan", "testing", "letmein", "secret", "football", "abc123",
  "admin123", "password123", "root", "master", "charlie"
];

export function evaluatePassword(password: string): PasswordFeedback {
  const length = password.length;

  let lowercaseCount = 0;
  let uppercaseCount = 0;
  let numberCount = 0;
  let symbolCount = 0;

  for (let i = 0; i < length; i++) {
    const ch = password[i];
    if (/[a-z]/.test(ch)) lowercaseCount++;
    else if (/[A-Z]/.test(ch)) uppercaseCount++;
    else if (/[0-9]/.test(ch)) numberCount++;
    else symbolCount++;
  }

  const hasLowercase = lowercaseCount > 0;
  const hasUppercase = uppercaseCount > 0;
  const hasNumber = numberCount > 0;
  const hasSpecial = symbolCount > 0;
  const hasMinLength = length >= 12;

  const warnings: string[] = [];
  const suggestions: string[] = [];

  if (length === 0) {
    return {
      score: 0,
      scorePercent: 0,
      tier: "Very Weak",
      colorClass: "text-slate-400",
      accentColor: "#94a3b8",
      hasMinLength: false,
      hasUppercase: false,
      hasLowercase: false,
      hasNumber: false,
      hasSpecial: false,
      length: 0,
      counts: { lowercase: 0, uppercase: 0, numbers: 0, symbols: 0 },
      criteria: [
        { id: "length", name: "Length (12+)", met: false, score: 0, detail: "0 / 12 characters", category: "length" },
        { id: "uppercase", name: "Uppercase (A-Z)", met: false, score: 0, detail: "0 found", category: "uppercase" },
        { id: "lowercase", name: "Lowercase (a-z)", met: false, score: 0, detail: "0 found", category: "lowercase" },
        { id: "numbers", name: "Numbers (0-9)", met: false, score: 0, detail: "0 found", category: "numbers" },
        { id: "symbols", name: "Symbols (!@#$)", met: false, score: 0, detail: "0 found", category: "symbols" },
      ],
      warnings: [],
      suggestions: ["Type or paste a password to analyze its strength interactively."],
      entropyBits: 0,
      timeToCrack: "Instant",
    };
  }

  // Calculate pool size
  let poolSize = 0;
  if (hasLowercase) poolSize += 26;
  if (hasUppercase) poolSize += 26;
  if (hasNumber) poolSize += 10;
  if (hasSpecial) poolSize += 33;
  if (poolSize === 0) poolSize = 1;

  // Shannon entropy
  let entropy = length * Math.log2(poolSize);

  // Repetition penalty
  const repeated = /(.)\1{2,}/.test(password);
  if (repeated) {
    warnings.push("Contains repeated identical characters (e.g. 'aaa').");
    entropy -= 12;
  }

  // Sequential character penalty (e.g. abc, 123)
  const lower = password.toLowerCase();
  for (let i = 0; i < lower.length - 2; i++) {
    const code1 = lower.charCodeAt(i);
    const code2 = lower.charCodeAt(i + 1);
    const code3 = lower.charCodeAt(i + 2);
    if (code2 === code1 + 1 && code3 === code2 + 1) {
      warnings.push("Contains sequential characters (e.g. '123' or 'abc').");
      entropy -= 10;
      break;
    }
  }

  // Dictionary words penalty
  for (const pattern of COMMON_PATTERNS) {
    if (lower.includes(pattern)) {
      warnings.push(`Contains commonly guessed sequence ('${pattern}').`);
      entropy -= 18;
      break;
    }
  }

  // Specific Suggestions
  if (length < 8) {
    warnings.push("Critically short: passwords under 8 characters can be brute-forced in seconds.");
    suggestions.push("Increase password length to at least 12–16 characters.");
  } else if (length < 12) {
    suggestions.push("Aim for 14+ characters to withstand GPU-accelerated hash cracking.");
  }

  if (!hasUppercase) suggestions.push("Add uppercase letters (A–Z) to expand character pool.");
  if (!hasLowercase) suggestions.push("Add lowercase letters (a–z).");
  if (!hasNumber) suggestions.push("Include numeric digits (0–9).");
  if (!hasSpecial) suggestions.push("Add punctuation or special symbols (!@#$%^&*).");

  entropy = Math.max(0, entropy);

  // Criteria scoring
  const lengthScore = Math.min(100, Math.round((length / 16) * 100));
  const upperScore = hasUppercase ? 100 : 0;
  const lowerScore = hasLowercase ? 100 : 0;
  const numScore = hasNumber ? 100 : 0;
  const symScore = hasSpecial ? 100 : 0;

  const criteria: CriteriaItem[] = [
    {
      id: "length",
      name: "Length (12+)",
      met: hasMinLength,
      score: lengthScore,
      detail: `${length} characters (${length >= 14 ? "Excellent" : length >= 12 ? "Good" : length >= 8 ? "Fair" : "Short"})`,
      category: "length",
    },
    {
      id: "uppercase",
      name: "Uppercase (A-Z)",
      met: hasUppercase,
      score: upperScore,
      detail: uppercaseCount > 0 ? `${uppercaseCount} uppercase letter${uppercaseCount > 1 ? "s" : ""}` : "Missing uppercase",
      category: "uppercase",
    },
    {
      id: "lowercase",
      name: "Lowercase (a-z)",
      met: hasLowercase,
      score: lowerScore,
      detail: lowercaseCount > 0 ? `${lowercaseCount} lowercase letter${lowercaseCount > 1 ? "s" : ""}` : "Missing lowercase",
      category: "lowercase",
    },
    {
      id: "numbers",
      name: "Numbers (0-9)",
      met: hasNumber,
      score: numScore,
      detail: numberCount > 0 ? `${numberCount} number${numberCount > 1 ? "s" : ""}` : "Missing numbers",
      category: "numbers",
    },
    {
      id: "symbols",
      name: "Symbols (!@#$)",
      met: hasSpecial,
      score: symScore,
      detail: symbolCount > 0 ? `${symbolCount} symbol${symbolCount > 1 ? "s" : ""}` : "Missing symbols",
      category: "symbols",
    },
  ];

  // Overall Score & Tier Determination
  let score = 0;
  let scorePercent = 0;
  let tier: PasswordFeedback["tier"] = "Very Weak";
  let colorClass = "text-rose-400";
  let accentColor = "#f43f5e";
  let timeToCrack = "Under 1 second";

  if (length >= 6 && entropy >= 20) {
    score = 1;
    scorePercent = 25;
    tier = "Weak";
    colorClass = "text-orange-400";
    accentColor = "#fb923c";
    timeToCrack = "A few minutes";
  }

  if (length >= 9 && entropy >= 42 && (hasUppercase || hasSpecial) && (hasNumber || hasLowercase)) {
    score = 2;
    scorePercent = 50;
    tier = "Moderate";
    colorClass = "text-amber-300";
    accentColor = "#facc15";
    timeToCrack = "Several days";
  }

  if (length >= 12 && entropy >= 62 && warnings.length === 0) {
    score = 3;
    scorePercent = 75;
    tier = "Strong";
    colorClass = "text-sky-300";
    accentColor = "#38bdf8";
    timeToCrack = "Thousands of years";
  }

  if (length >= 14 && entropy >= 80 && warnings.length === 0 && hasUppercase && hasLowercase && hasNumber && hasSpecial) {
    score = 4;
    scorePercent = 100;
    tier = "Very Strong";
    colorClass = "text-emerald-300";
    accentColor = "#38dea9";
    timeToCrack = "Millions of years";
  }

  return {
    score,
    scorePercent,
    tier,
    colorClass,
    accentColor,
    hasMinLength,
    hasUppercase,
    hasLowercase,
    hasNumber,
    hasSpecial,
    length,
    counts: {
      lowercase: lowercaseCount,
      uppercase: uppercaseCount,
      numbers: numberCount,
      symbols: symbolCount,
    },
    criteria,
    warnings,
    suggestions,
    entropyBits: Math.round(entropy),
    timeToCrack,
  };
}

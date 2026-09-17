// Small, MVP-level profanity filter for the text chat overlay.
// Not exhaustive — swap for a proper moderation API/library at scale
// (see build guide Phase 9, Step 9.4's note on frame-sampling moderation
// for video, which this file does not attempt to solve).

const BLOCKED_WORDS = [
  "fuck",
  "shit",
  "bitch",
  "asshole",
  "bastard",
  "cunt",
  "slut",
  "whore",
];

function filterProfanity(text) {
  let clean = text;
  for (const word of BLOCKED_WORDS) {
    const pattern = new RegExp(word, "gi");
    clean = clean.replace(pattern, "*".repeat(word.length));
  }
  return clean;
}

module.exports = { filterProfanity };

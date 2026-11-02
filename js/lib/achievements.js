// Achievements: fixed milestones computed from this browser's own progress. Nothing here is stored;
// an achievement is earned the moment its condition is true, so nothing needs migrating for old progress.
import { KYU, LADDER } from "./ranks.js";

const solvedCount = (S) => Object.keys(S.solved).length;
const sweepsKyu = (S, LISTED, k) => {
  const at = LISTED.filter((p) => p.kyu === k);
  return at.length > 0 && at.every((p) => S.solved[p.id]);
};

export const ACHIEVEMENTS = [
  { id: "first-solve", title: "First blood", note: "Solve your first problem.", earned: (S) => solvedCount(S) >= 1 },
  { id: "first-proof", title: "Prover", note: "Submit a proof for review.", earned: (S) => Object.values(S.proofs).some((p) => p.submitted) },
  { id: "ten-solved", title: "Warming up", note: "Solve 10 problems.", earned: (S) => solvedCount(S) >= 10 },
  { id: "fifty-solved", title: "Well drilled", note: "Solve 50 problems.", earned: (S) => solvedCount(S) >= 50 },
  { id: "streak-7", title: "A week of it", note: "Reach a 7 day streak.", earned: (S, LISTED, streak) => streak >= 7 },
  { id: "streak-30", title: "A month of it", note: "Reach a 30 day streak.", earned: (S, LISTED, streak) => streak >= 30 },
  { id: "no-hints", title: "Unaided", note: "Solve 10 problems without opening a hint.", earned: (S) => Object.entries(S.solved).filter(([id]) => !S.hints[id]).length >= 10 },
  { id: "duel-win", title: "Duellist", note: "Win a duel.", earned: (S) => S.duel.w >= 1 },
  { id: "favourite-5", title: "Curator", note: "Favourite 5 problems.", earned: (S) => Object.keys(S.favourites).length >= 5 },
  ...LADDER.map((k) => ({ id: `sweep-${k}`, title: `${KYU[k].belt} belt clear`, note: `Solve every ${k} kyu problem in the bank.`, earned: (S, LISTED) => sweepsKyu(S, LISTED, k) })),
];

export const earnedAchievements = (S, LISTED, streak) => ACHIEVEMENTS.filter((a) => a.earned(S, LISTED, streak));

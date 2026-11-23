type KeywordPaper = { id: string; title: string; status: string };

const stopWords = new Set(('a an the of in on at to for from with and or as by is are be how what when where why evidence effects effect impact role study analysis new using does do can through within across under towards toward their its our your this that more less two three versus if you we us i s u').split(' '));
const genericWords = new Set(['evidence', 'study', 'analysis', 'effect', 'effects', 'impact']);
const acronyms: Record<string, string> = { ai: 'AI', esg: 'ESG', ceo: 'CEO', cfo: 'CFO', ipo: 'IPO', etf: 'ETF', sec: 'SEC', csr: 'CSR', 'r&d': 'R&D' };

// Each title contributes a phrase once, even when it repeats within that title.
export function titlePhrases(title: string): Set<string> {
  const words = title.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/labour/g, 'labor').replace(/[’‘]/g, "'").match(/r&d|[a-z]+(?:'[a-z]+)?/g) || [];
  const phrases = new Set<string>();
  for (let size = 2; size <= 4; size++) {
    for (let start = 0; start + size <= words.length; start++) {
      const phrase = words.slice(start, start + size);
      if (stopWords.has(phrase[0]) || stopWords.has(phrase[phrase.length - 1])) continue;
      if (phrase.filter(word => word.length > 1 && !stopWords.has(word)).length < 2) continue;
      if (phrase.some(word => genericWords.has(word))) continue;
      phrases.add(phrase.join(' '));
    }
  }
  return phrases;
}

function label(phrase: string): string {
  return phrase.split(' ').map(word => acronyms[word] || word[0].toUpperCase() + word.slice(1)).join(' ');
}

// Vocabulary is based only on strict R&R papers, recurring in at least two.
// Recomputing from titles lets weekly paper-data updates refresh this module.
export function buildPaperKeywords(papers: readonly KeywordPaper[]): Map<string, string[]> {
  const phrases = new Map(papers.map(paper => [paper.id, titlePhrases(paper.title)]));
  const counts = new Map<string, number>();
  for (const paper of papers) {
    if (paper.status !== 'R&R') continue;
    for (const phrase of phrases.get(paper.id) || []) counts.set(phrase, (counts.get(phrase) || 0) + 1);
  }
  return new Map(papers.map(paper => [paper.id, [...(phrases.get(paper.id) || [])].filter(phrase => (counts.get(phrase) || 0) >= 2).map(label)]));
}

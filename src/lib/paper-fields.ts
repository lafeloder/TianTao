import type { Paper } from '../types/watchlists';

// These are browsing aids, not journal-assigned research classifications.
// Use only the paper's own tags and title; source excerpts may name other papers.
export const paperFields = [
  'Banking',
  'Corporate Finance',
  'Asset Pricing',
  'Asset Management',
  'Household Finance',
  'Market Microstructure',
  'International Finance',
  'Sustainable Finance',
  'FinTech & AI',
  'Real Estate',
  'Labor & Human Capital',
  'Public Finance',
  'Macro-Finance',
  'Accounting & Disclosure',
  'Behavioral Finance',
  'Operations & Management',
  'Unclassified',
] as const;

export type PaperField = typeof paperFields[number];

const fieldRules: Partial<Record<PaperField, RegExp>> = {
  Banking: /\bbanks?\b|\bbanking\b|\bnon[ -]?banks?\b|\bdeposits?\b|\bdepositors?\b|\blending\b|\bloans?\b|\bcredit (?:supply|markets?|transmission|cycle|reallocation|equality|reports?)\b|\bsecuriti[sz]ation\b|\bintermediat\w*\b|\bcollateral\b|\bmortgages?\b|\bprudential\b|\bbailouts?\b|\bfinancial stability\b/i,
  'Corporate Finance': /\bcorporate\b|\bfirms?\b|\bcapital structure\b|\bgovernance\b|\bboards?\b|\bdirectors?\b|\bshareholders?\b|\bexecutives?\b|\bceos?\b|\bmanagerial\b|\bentrepreneur\w*\b|\bventure\b|\bstart[ -]?ups?\b|\bmergers?\b|\bacquisitions?\b|\bdividends?\b|\bpayout\b|\brestructuring\b|\bbankrupt\w*\b|\br\s*&\s*d\b/i,
  'Asset Pricing': /\basset pric\w*\b|\basset values?\b|\brisk premi\w*\b|\b(?:profitability|equity|volatility|bond) premium\b|\breturns?\b|\bvolatilit\w*\b|\bvaluations?\b|\bdiscount (?:rates?|factors?)\b|\brisk factors?\b|\bfactor (?:models?|spanning)\b|\bterm structures?\b|\byield curves?\b|\bstock prices?\b|\balpha\b|\barbitrage\b|\bmispricing\b|\bmomentum\b|\banomal\w*\b/i,
  'Asset Management': /\bmutual funds?\b|\bhedge funds?\b|\bfund (?:managers?|runs?|flows?|fragility|skill|industry|marketing)\b|\bportfolios?\b|\betfs?\b|\binstitutional (?:investors?|trading)\b|\bprivate equity\b|\bindex (?:invest\w*|funds?)\b|\bpassive (?:invest\w*|funds?)\b|\bventure (?:capital|investors?)\b|\basset management\b/i,
  'Household Finance': /\bhouseholds?\b|\bconsumers?\b|\bretail investors?\b|\bpersonal financ\w*\b|\bfinancial advi\w*\b|\brobo[ -]?advi\w*\b|\bfinancial education\b|\bfinancial literacy\b|\bretirement\b|\bpensions?\b|\bstudent (?:debt|loans?)\b|\bcredit cards?\b|\bpayday\b|\bfamil(?:y|ies)\b|\bsavings?\b|\bhome equity\b|\b401\(k\)/i,
  'Market Microstructure': /\btrading\b|\bmarket makers?\b|\border (?:books?|flow|routing)\b|\blimit orders?\b|\bquotes?\b|\bbid[ -]?ask\b|\bprice (?:discovery|impact|revelation|dispersion)\b|\bexchange data\b|\boff[ -]exchange\b|\bbest execution\b|\bmarket fragmentation\b|\bliquidity (?:provision|supply)\b|\bshort sell\w*\b|\bquote competition\b/i,
  'International Finance': /\bforeign\b|\bcurrenc\w*\b|\bexchange rates?\b|\bcross[ -]border\b|\binternational\b|\bglobal (?:bank\w*|financ\w*)\b|\bsovereign\b|\bdollars?\b|\bcapital flows?\b|\bgeopolitic\w*\b|\bfx\b/i,
  'Sustainable Finance': /\bclimate\b|\bsustainab\w*\b|\bbiodiversity\b|\bcarbon\b|\bgreen\b|\besg\b|\brenewable\b|\bpollution\b|\bemissions?\b|\bclean air\b|\bwetlands?\b|\bflood risk\b|\bnatural disasters?\b|\bnatural capital\b|\bbrown capital\b/i,
  'FinTech & AI': /\bfintech\b|\bai\b|\bartificial intelligence\b|\bmachine learning\b|\brobo[ -]?advi\w*\b|\bcrypto\w*\b|\bbitcoin\b|\bblockchain\b|\bdigital (?:currenc\w*|assets?|ownership)\b|\bstablecoins?\b|\bdistributed ledgers?\b|\bchatgpt\b|\bgenerative\b|\be[ -]money\b|\bonline (?:banks?|lending)\b|\bopen banking\b|\btokeni[sz]\w*\b|\bautomated underwriting\b|\bpayment convenience\b|\bcbdcs?\b/i,
  'Real Estate': /\bhousing\b|\bmortgages?\b|\bhouse prices?\b|\breal estate\b|\bpropert(?:y|ies)\b|\bhome equity\b|\bland (?:allocation|\(mis\)allocation)\b|\breits?\b/i,
  'Labor & Human Capital': /\blabou?r\b|\bemployment\b|\bworkers?\b|\bwages?\b|\bhuman capital\b|\bhir(?:e|es|ing)\b|\bcareers?\b|\bjobs?\b|\bsick leave\b|\bunemployment\b|\bmotherhood\b|\bteam performance\b/i,
  'Public Finance': /\bmunicipal\b|\bpublic (?:debt|finance)\b|\btax(?:es|ation)?\b|\bfiscal\b|\btreasur(?:y|ies)\b|\bgovernment (?:guarantees?|support|debt)\b|\bsubsid\w*\b|\bschool finance\b|\blocal government\b/i,
  'Behavioral Finance': /\bbeliefs?\b|\bbehavio\w*\b|\bbias(?:es|ed)?\b|\boverconfidence\b|\battention\b|\bmental\b|\bexpectations?\b|\bextrapolat\w*\b|\bcognitiv\w*\b|\bsalience\b|\bnudg\w*\b|\bpreferences?\b|\bfinancial literacy\b|\bdisposition effect\b/i,
  'Operations & Management': /\bsupply chains?\b|\binventor(?:y|ies)\b|\boperations?\b|\bmanufactur\w*\b|\bproduction\b|\bdynamic pricing\b|\bassortments?\b|\bconsumer choice\b|\blicensing\b|\bmarketing\b|\badvertis\w*\b|\bplatforms?\b|\bproduct markets?\b|\bdemand estimation\b|\bdecision performance\b|\bdata[ -]driven decision\w*\b/i,
};

const topicAliases: Record<string, PaperField> = {
  'financial intermediation': 'Banking',
  labor: 'Labor & Human Capital',
  expectations: 'Behavioral Finance',
};

// Additional specific terms cover titles that do not use the field name.
const additionalRules: Partial<Record<PaperField, RegExp>> = {
  Banking: /\blenders?\b|\bcredit (?:agreements?|multipliers?|risk)\b|\brepo markets?\b|\breserves\b|\bbail[ -]in\b|\bsystemic risk\b|\bpaycheck protection program\b/i,
  'Corporate Finance': /\bipos?\b|\bleasing\b|\bproxy voting\b|\bfinancial constraints\b|\bfinancial flexibility\b|\bdebt structure\b|\brevenue[ -]based financing\b|\btunneling\b|\bco[ -]founding\b|\bintangibles?\b|\bcorporate bonds?\b|\binnovation\b|\bcreative destruction\b|\bcapital fundraising\b/i,
  'Asset Pricing': /\b(?:profitability|equity|volatility|bond) premiums?\b|\bfutures\b|\boptions? (?:trad\w*|pric\w*|mispric\w*)\b|\bderivatives?\b|\b(?:multi)?factor models?\b|\bfactor zoo\b|\bcomovement\b|\bco[ -]movement\b|\bpricing of (?:risk|news|near[ -]money)\b|\bstock market\b|\bstock selection\b|\bequity markets?\b|\bdefault risk\b|\branking stocks\b|\bhedging\b|\binvestor risk\b|\bequilibrium value\b|\brebalancing\b/i,
  'Asset Management': /\bmoney market funds?\b|\btarget[ -]date funds?\b|\bprivate capital fundraising\b|\bindexing\b|\brebalancing\b/i,
  'Household Finance': /\bconsumption\b|\bspending patterns\b|\bbuy now,? pay later\b|\bfinancial advice\b|\bstock market participation\b/i,
  'Market Microstructure': /\btraders?\b|\btrades\b|\bmarket efficien\w*\b|\bmarket effiici\w*\b|\bover[ -]the[ -]counter\b|\bdealers?\b|\bconsolidated feed\b|\bprice multipliers?\b|\bmarket become more liquid\b|\bprediction markets?\b|\binformed minority\b/i,
  'International Finance': /\bexorbitant privilege\b/i,
  'Sustainable Finance': /\bcap and trade\b/i,
  'FinTech & AI': /\bllms?\b|\bcybersecurity\b|\bdigital versus traditional\b|\bstaking\b/i,
  'Labor & Human Capital': /\btalent\b|\bco[ -]leadership\b|\bleadership participation\b/i,
  'Public Finance': /\bcity hall\b/i,
  'Macro-Finance': /\bmonetary\b|\binflation\b|\bcentral banks?\b|\bfederal reserve\b|\bfomc\b|\binterest rates?\b|\bbusiness cycles?\b|\bmacroeconom\w*\b/i,
  'Accounting & Disclosure': /\baccounting\b|\baudit\w*\b|\bdisclosure\b|\bfinancial reporting\b|\breporting discretion\b|\bearnings\b|\bpublic forecasts\b/i,
  'Behavioral Finance': /\breference points\b|\bfinancialization\b/i,
  'Operations & Management': /\bsupply[ -]chains?\b|\bprocurement\b|\border adjustments?\b|\bcommercialization\b|\bdecision making\b|\bpriority mechanisms?\b|\bordinal ratings\b/i,
};

// The title alone does not reveal this paper's bank-regulation setting.
const fieldOverrides: Record<string, PaperField[]> = {
  'author-roster-20261014-ec6c79c18c81': ['Banking'],
};

export function getPaperFields(paper: Pick<Paper, 'id' | 'title' | 'topics'>): PaperField[] {
  const fields = new Set<PaperField>(fieldOverrides[paper.id] || []);
  const title = paper.title.normalize('NFKC').replace(/[‐‑‒–—−]/g, '-');
  for (const topic of paper.topics || []) {
    const key = topic.trim().toLowerCase();
    const known = paperFields.find(field => field.toLowerCase() === key) || topicAliases[key];
    if (known && known !== 'Unclassified') fields.add(known);
  }
  for (const field of paperFields) {
    if (fieldRules[field]?.test(title) || additionalRules[field]?.test(title)) fields.add(field);
  }
  return fields.size ? paperFields.filter(field => fields.has(field)) : ['Unclassified'];
}

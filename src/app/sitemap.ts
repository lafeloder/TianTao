import type { MetadataRoute } from 'next';
import { getConfig } from '@/lib/config';
import { getPageConfig } from '@/lib/content';
import { getCanonicalUrl } from '@/lib/seo';
import type { BasePageConfig } from '@/types/page';

export const dynamic = 'force-static';

export default function sitemap(): MetadataRoute.Sitemap {
  const slugs = new Set(['', 'Top5RR', 'EuropePostdocs']);

  for (const item of getConfig().navigation) {
    if (item.type !== 'page' || item.target === 'about' || slugs.has(item.target)) continue;
    const page = getPageConfig<BasePageConfig>(item.target);
    // Empty/unsupported content pages render a 404 and must not be in the sitemap.
    if (page?.title && ['publication', 'text', 'card'].includes(page.type)) {
      slugs.add(item.target);
    }
  }

  return [...slugs].map((slug) => ({ url: getCanonicalUrl(slug) }));
}

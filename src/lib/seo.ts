import type { Metadata } from 'next';
import { getConfig } from '@/lib/config';
import { getRuntimeI18nConfig } from '@/lib/i18n/config';

// Keep the GitHub Pages project path and trailing slash in every page URL.
export function getCanonicalUrl(slug = ''): string {
  const baseUrl = `${getConfig().site.url.replace(/\/+$/, '')}/`;
  const pagePath = slug.replace(/^\/+|\/+$/g, '');
  return new URL(pagePath ? `${pagePath.split('/').map(encodeURIComponent).join('/')}/` : '', baseUrl).href;
}

export function getPageMetadata(slug: string, title: string, description: string): Metadata {
  const config = getConfig();
  const runtimeI18n = getRuntimeI18nConfig(config.i18n);
  const fullTitle = slug ? `${title} | ${config.author.name}` : title;

  return {
    title: { absolute: fullTitle },
    description,
    alternates: { canonical: getCanonicalUrl(slug) },
    openGraph: {
      type: 'website',
      locale: runtimeI18n.defaultLocale === 'zh' ? 'zh_CN' : 'en_US',
      siteName: config.site.title,
      title: fullTitle,
      description,
      url: getCanonicalUrl(slug),
    },
    twitter: {
      card: 'summary',
      title: fullTitle,
      description,
    },
  };
}

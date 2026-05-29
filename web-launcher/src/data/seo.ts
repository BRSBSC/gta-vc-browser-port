export const SITE_URL = 'https://www.gtavice.city';
export const CANONICAL = `${SITE_URL}/`;
export const OG_IMAGE = `${SITE_URL}/og-image.png`;
export const FAVICON = '/icon.ico';
export const LOGO = '/vice-city-logo.webp';
export const MANIFEST = '/manifest.webmanifest';
export const SITEMAP = '/sitemap-index.xml';
export const GA_MEASUREMENT_ID = 'G-GNHJPLHH37';

export const seo = {
  title: 'Play GTA Vice City Online Free - Instant, No Download',
  description: 'Play GTA Vice City online free. Step into 1980s Miami, drive classic cars, run missions in the open-world crime classic. No download, instant play.',
  ogTitle: 'GTA Vice City Online - Play Free, No Download',
  ogDescription: 'Step into 1980s Miami. Play GTA Vice City online free, drive classic cars, run missions, blast through neon-lit streets. Just click play.',
  twitterDescription: 'Play GTA Vice City online free. 1980s Miami, classic cars, open world. No download, instant play.',
  keywords: 'GTA Vice City online, play Vice City free, GTA Vice City browser, GTA Vice City no download, Vice City unblocked, play GTA Vice City instantly, Grand Theft Auto Vice City online, classic GTA online, 1980s Miami game',
  siteName: 'GTA Vice City Online',
  locale: 'en_US',
  themeColor: '#0a0a1a',
  backgroundColor: '#06010c',
  ogImageAlt: 'GTA Vice City Online - play free in your browser, no download',
} as const;

export const videoGameSchema = {
  '@context': 'https://schema.org',
  '@type': 'VideoGame',
  name: 'GTA Vice City Online',
  alternateName: ['Grand Theft Auto: Vice City Online', 'GTA Vice City Free Online', 'Vice City Online'],
  description: seo.description,
  url: SITE_URL,
  image: OG_IMAGE,
  applicationCategory: 'Game',
  operatingSystem: 'Web Browser',
  gamePlatform: 'Web Browser',
  genre: ['Action-Adventure', 'Open World', 'Crime'],
  playMode: 'SinglePlayer',
  inLanguage: 'en',
  isAccessibleForFree: true,
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
    availability: 'https://schema.org/InStock',
    url: SITE_URL,
  },
  publisher: {
    '@type': 'Organization',
    name: 'gtavice.city',
    url: SITE_URL,
  },
  disambiguatingDescription: 'Unofficial fan project. Not affiliated with or endorsed by Rockstar Games or Take-Two Interactive.',
} as const;

export const webAppSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebApplication',
  name: 'GTA Vice City Online',
  description: 'Play GTA Vice City online free in your browser. No download, no install, just click play.',
  url: SITE_URL,
  applicationCategory: 'GameApplication',
  operatingSystem: 'Web Browser',
  isAccessibleForFree: true,
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
} as const;

export const websiteSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: seo.siteName,
  url: SITE_URL,
  inLanguage: 'en',
  publisher: {
    '@type': 'Organization',
    name: 'gtavice.city',
    url: SITE_URL,
  },
} as const;

import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://www.gtavice.city',
  trailingSlash: 'never',
  server: {
    port: 4321,
    host: true,
  },
  devToolbar: {
    enabled: false,
  },
});

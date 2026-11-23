import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Um namespace por arquivo em ./locales/pt-BR/*.json (ex.: common.json -> 'common').
// Convenção: um namespace por página/componente (useTranslation('chapters')), chaves em camelCase.
const modules = import.meta.glob('./locales/pt-BR/*.json', { eager: true, import: 'default' }) as Record<
  string,
  Record<string, unknown>
>;

const resources: Record<string, Record<string, Record<string, unknown>>> = { 'pt-BR': {} };
for (const [path, content] of Object.entries(modules)) {
  const namespace = path.split('/').pop()!.replace(/\.json$/, '');
  resources['pt-BR'][namespace] = content;
}

void i18n.use(initReactI18next).init({
  resources,
  lng: 'pt-BR',
  fallbackLng: 'pt-BR',
  defaultNS: 'common',
  ns: Object.keys(resources['pt-BR']),
  interpolation: { escapeValue: false },
});

export default i18n;

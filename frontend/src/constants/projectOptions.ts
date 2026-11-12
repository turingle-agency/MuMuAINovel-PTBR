// Opções compartilhadas de projeto (idioma do conteúdo, perspectiva narrativa e gêneros).

export type ProjectLanguage = 'pt-BR' | 'en-US' | 'es-ES' | 'es-MX';

// Espelha SUPPORTED_LANGUAGES do backend.
export const LANGUAGE_OPTIONS: { value: ProjectLanguage; label: string }[] = [
  { value: 'pt-BR', label: 'Português (Brasil)' },
  { value: 'en-US', label: 'English (United States)' },
  { value: 'es-ES', label: 'Español (España)' },
  { value: 'es-MX', label: 'Español (México)' },
];

export const DEFAULT_LANGUAGE: ProjectLanguage = 'pt-BR';

// Valores aceitos pelo backend para a perspectiva narrativa.
export const NARRATIVE_PERSPECTIVE_OPTIONS = [
  { value: 'primeira pessoa', label: 'Primeira pessoa' },
  { value: 'terceira pessoa', label: 'Terceira pessoa' },
  { value: 'onisciente', label: 'Onisciente' },
];

export const DEFAULT_NARRATIVE_PERSPECTIVE = 'terceira pessoa';

export const GENRE_OPTIONS = [
  'Fantasia',
  'Ficção científica',
  'Romance',
  'Suspense',
  'Mistério',
  'Terror',
  'Histórico',
  'Aventura',
  'Drama',
  'Policial',
];

// Normaliza valores legados (chinês: 1ª pessoa, 3ª pessoa, onisciente) para os valores em português.
const LEGACY_PERSPECTIVES: Record<string, string> = {
  '\u7b2c\u4e00\u4eba\u79f0': 'primeira pessoa',
  '\u7b2c\u4e09\u4eba\u79f0': 'terceira pessoa',
  '\u5168\u77e5\u89c6\u89d2': 'onisciente',
};

export function normalizePerspective(value?: string | null): string {
  if (!value) return DEFAULT_NARRATIVE_PERSPECTIVE;
  return LEGACY_PERSPECTIVES[value] ?? value;
}

// Converte o rótulo exibido (ou texto livre digitado) no valor enviado ao backend.
export function perspectiveFromLabel(label: string): string {
  const text = label.trim();
  const option = NARRATIVE_PERSPECTIVE_OPTIONS.find((item) => item.label.toLowerCase() === text.toLowerCase());
  return option ? option.value : normalizePerspective(text);
}

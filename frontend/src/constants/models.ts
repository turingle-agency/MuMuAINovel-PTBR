// Modelos de IA padrão. Espelho de backend/app/constants/models.py (fonte única de verdade).
// Ao atualizar, altere os dois arquivos e a data MODELS_CHECKED_AT.
export const MODELS_CHECKED_AT = '2026-11-12';

export const DEFAULT_TEXT_MODELS: Record<string, string> = {
  openai: 'gpt-6.1-terra',
  anthropic: 'claude-sonnet-5-5',
  gemini: 'gemini-3.8-flash',
};

export const DEFAULT_COVER_MODELS: Record<string, string> = {
  gemini: 'gemini-3.1-flash-image',
  grok: 'grok-imagine-image',
};

export const defaultTextModel = (provider?: string | null): string =>
  DEFAULT_TEXT_MODELS[(provider || '').toLowerCase().trim()] ?? DEFAULT_TEXT_MODELS.openai;

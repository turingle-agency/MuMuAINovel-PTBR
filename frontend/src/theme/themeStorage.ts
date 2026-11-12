export type ThemeMode = 'light' | 'dark' | 'system';

const THEME_MODE_STORAGE_KEY = 'mumu_theme_mode';

const isThemeMode = (value: string | null): value is ThemeMode => {
  return value === 'light' || value === 'dark' || value === 'system';
};

export const getStoredThemeMode = (): ThemeMode => {
  try {
    const value = localStorage.getItem(THEME_MODE_STORAGE_KEY);
    if (isThemeMode(value)) {
      return value;
    }
  } catch (error) {
    console.warn('Falha ao ler o modo de tema:', error);
  }

  return 'system';
};

export const setStoredThemeMode = (mode: ThemeMode): void => {
  try {
    localStorage.setItem(THEME_MODE_STORAGE_KEY, mode);
  } catch (error) {
    console.warn('Falha ao salvar o modo de tema:', error);
  }
};

export const getThemeModeStorageKey = (): string => THEME_MODE_STORAGE_KEY;

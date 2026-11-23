import { Segmented, Tooltip } from 'antd';
import { BulbOutlined, MoonOutlined, DesktopOutlined } from '@ant-design/icons';
import { useThemeMode } from '../theme/useThemeMode';
import type { ThemeMode } from '../theme/themeStorage';
import type { ReactNode } from 'react';
import i18n from '../i18n';

interface ThemeSwitchProps {
  size?: 'small' | 'middle' | 'large';
  block?: boolean;
}

const options: Array<{ value: ThemeMode; label: ReactNode }> = [
  {
    value: 'light',
    label: (
      <Tooltip title={i18n.t('themeSwitch:modoClaro')}>
        <BulbOutlined />
      </Tooltip>
    ),
  },
  {
    value: 'dark',
    label: (
      <Tooltip title={i18n.t('themeSwitch:modoEscuro')}>
        <MoonOutlined />
      </Tooltip>
    ),
  },
  {
    value: 'system',
    label: (
      <Tooltip title={i18n.t('themeSwitch:seguirOSistema')}>
        <DesktopOutlined />
      </Tooltip>
    ),
  },
];

export default function ThemeSwitch({ size = 'middle', block = false }: ThemeSwitchProps) {
  const { mode, setMode } = useThemeMode();

  return (
    <Segmented
      size={size}
      value={mode}
      onChange={(value) => setMode(value as ThemeMode)}
      options={options}
      block={block}
    />
  );
}

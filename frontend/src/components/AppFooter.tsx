import { useTranslation } from 'react-i18next';
import { Typography, Space, Divider, Grid, theme } from 'antd';
import { GithubOutlined, CopyrightOutlined, HeartFilled, ClockCircleOutlined } from '@ant-design/icons';
import { VERSION_INFO, getVersionString } from '../config/version';

const { Text, Link } = Typography;
const { useBreakpoint } = Grid;

interface AppFooterProps {
  sidebarWidth?: number;
}

export default function AppFooter({ sidebarWidth = 0 }: AppFooterProps) {
  const screens = useBreakpoint();
  const isMobile = !screens.md;
  const { t } = useTranslation('common');
  const { token } = theme.useToken();
  const alphaColor = (color: string, alpha: number) => `color-mix(in srgb, ${color} ${(alpha * 100).toFixed(0)}%, transparent)`;

  // Margem esquerda: no desktop com barra lateral é preciso deslocar
  const leftOffset = isMobile ? 0 : sidebarWidth;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: leftOffset,
        right: 0,
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderTop: `1px solid ${token.colorBorder}`,
        padding: isMobile ? '8px 12px' : '10px 16px',
        zIndex: 100,
        boxShadow: `0 -2px 16px ${alphaColor(token.colorText, 0.08)}`,
        backgroundColor: alphaColor(token.colorBgContainer, 0.82), // fundo translúcido para o backdrop-filter
        transition: 'left 0.3s ease',
      }}
    >
      <div
        style={{
          maxWidth: 1400,
          margin: '0 auto',
          textAlign: 'center',
        }}
      >
        {isMobile ? (
          // Mobile: linha única compacta
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 8,
            flexWrap: 'wrap'
          }}>
            <Text
              style={{
                fontSize: 11,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: token.colorPrimary,
              }}
              title={t('footer.currentVersion')}
            >
              <strong style={{ color: token.colorText }}>{VERSION_INFO.projectName}</strong>
              <span>{getVersionString()}</span>
            </Text>
            <Divider type="vertical" style={{ margin: '0 4px', borderColor: token.colorBorder }} />
            <Link
              href={VERSION_INFO.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 11,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: token.colorTextSecondary,
              }}
            >
              <GithubOutlined style={{ fontSize: 12 }} />
            </Link>
            <Text
              style={{
                fontSize: 10,
                color: token.colorTextTertiary,
              }}
            >
              <ClockCircleOutlined style={{ fontSize: 10, marginRight: 4 }} />
              {VERSION_INFO.buildTime}
            </Text>
          </div>
        ) : (
          // Desktop: layout completo
          <Space
            direction="horizontal"
            size={12}
            split={<Divider type="vertical" style={{ borderColor: token.colorBorder }} />}
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}
          >
            {/* Versão */}
            <Text
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: token.colorTextSecondary,
              }}
              title={t('footer.currentVersion')}
            >
              <strong style={{ color: token.colorText }}>{VERSION_INFO.projectName}</strong>
              <span>{getVersionString()}</span>
            </Text>

            {/* Link do repositório */}
            <Link
              href={VERSION_INFO.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: token.colorTextSecondary,
              }}
            >
              <GithubOutlined style={{ fontSize: 13 }} />
              <span>GitHub</span>
            </Link>

            {/* Licença */}
            <Link
              href={VERSION_INFO.licenseUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: token.colorTextSecondary,
              }}
            >
              <CopyrightOutlined style={{ fontSize: 11 }} />
              <span>{VERSION_INFO.license}</span>
            </Link>

            {/* Data do build */}
            <Text
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: token.colorTextTertiary,
              }}
            >
              <ClockCircleOutlined style={{ fontSize: 12 }} />
              <span>{VERSION_INFO.buildTime}</span>
            </Text>

            {/* Créditos */}
            <Text
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: token.colorTextSecondary,
                textShadow: `0 1px 3px ${alphaColor(token.colorText, 0.08)}`,
              }}
            >
              <span>{t('footer.basedOn')}</span>
              <HeartFilled style={{ color: token.colorError, fontSize: 11 }} />
              <span>{VERSION_INFO.author}</span>
            </Text>
          </Space>
        )}
      </div>
    </div>
  );
}

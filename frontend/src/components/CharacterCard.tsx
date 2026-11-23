import { Card, Space, Tag, Typography, Popconfirm, theme } from 'antd';
import { EditOutlined, DeleteOutlined, UserOutlined, BankOutlined, ExportOutlined } from '@ant-design/icons';
import { characterCardStyles } from './CardStyles';
import type { Character } from '../types';
import { useTranslation } from 'react-i18next';

const { Text, Paragraph } = Typography;

interface CharacterCardProps {
  character: Character;
  onEdit?: (character: Character) => void;
  onDelete: (id: string) => void;
  onExport?: () => void;
}

export const CharacterCard: React.FC<CharacterCardProps> = ({ character, onEdit, onDelete, onExport }) => {
  const { t } = useTranslation('characterCard');
  const { token } = theme.useToken();

  const getRoleTypeColor = (roleType?: string) => {
    const roleColors: Record<string, string> = {
      'protagonist': 'blue',
      'supporting': 'green',
      'antagonist': 'red',
    };
    return roleColors[roleType || ''] || 'default';
  };

  const getRoleTypeLabel = (roleType?: string) => {
    const roleLabels: Record<string, string> = {
      'protagonist': t('protagonista'),
      'supporting': t('coadjuvante'),
      'antagonist': t('antagonista'),
    };
    return roleLabels[roleType || ''] || t('outro');
  };

  const isOrganization = character.is_organization;
  const charStatus = character.status || 'active';
  const isInactive = charStatus !== 'active';

  const getStatusTag = () => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      deceased: { color: token.colorTextBase, label: t('morto') },
      missing: { color: token.colorWarning, label: t('desaparecido') },
      retired: { color: token.colorTextTertiary, label: t('foraDeCena') },
      destroyed: { color: token.colorTextBase, label: t('aniquilada') },
    };
    const config = statusConfig[charStatus];
    if (!config) return null;
    return <Tag color={config.color} style={{ marginLeft: 4 }}>{config.label}</Tag>;
  };

  return (
    <Card
      hoverable
      style={{
        ...(isOrganization ? characterCardStyles.organizationCard : characterCardStyles.characterCard),
        ...(isInactive ? { opacity: 0.6, filter: 'grayscale(40%)' } : {}),
      }}
      styles={{
        body: {
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column'
        },
        actions: {
          borderRadius: '0 0 12px 12px'
        }
      }}
      actions={[
        ...(onEdit ? [<EditOutlined key="edit" onClick={() => onEdit(character)} />] : []),
        ...(onExport ? [<ExportOutlined key="export" onClick={onExport} />] : []),
        <Popconfirm
          key="delete"
          title={t('temCertezaDesejaExcluir', { valor: isOrganization ? t('estaOrganizacao') : t('estePersonagem') })}
          onConfirm={() => onDelete(character.id)}
          okText={t('confirmar')}
          cancelText={t('cancelar')}
        >
          <DeleteOutlined />
        </Popconfirm>,
      ]}
    >
      <Card.Meta
        avatar={
          isOrganization ? (
            <BankOutlined style={{ fontSize: 32, color: token.colorSuccess }} />
          ) : (
            <UserOutlined style={{ fontSize: 32, color: token.colorPrimary }} />
          )
        }
        title={
          <Space>
            <span style={characterCardStyles.nameEllipsis}>{character.name}</span>
            {isOrganization ? (
              <Tag color="green">{t('estaOrganizacao')}</Tag>
            ) : (
              character.role_type && (
                <Tag color={getRoleTypeColor(character.role_type)}>
                  {getRoleTypeLabel(character.role_type)}
                </Tag>
              )
            )}
            {getStatusTag()}
          </Space>
        }
        description={
          <div style={characterCardStyles.descriptionBlock}>
            {/* 角色特有字段 */}
            {!isOrganization && (
              <>
                {character.age && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('idade')}</Text>
                    <Text style={{ flex: 1 }}>{character.age}</Text>
                  </div>
                )}
                {character.gender && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('genero')}</Text>
                    <Text style={{ flex: 1 }}>{character.gender}</Text>
                  </div>
                )}
                {character.personality && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('personalidade')}</Text>
                    <Text
                      style={{ flex: 1, minWidth: 0 }}
                      ellipsis={{ tooltip: character.personality }}
                    >
                      {character.personality}
                    </Text>
                  </div>
                )}
                {character.relationships && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('relacoes')}</Text>
                    <Text
                      style={{ flex: 1, minWidth: 0 }}
                      ellipsis={{ tooltip: character.relationships }}
                    >
                      {character.relationships}
                    </Text>
                  </div>
                )}
              </>
            )}

            {/* 组织特有字段 */}
            {isOrganization && (
              <>
                {character.organization_type && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('tipo')}</Text>
                    <Tag color="cyan">{character.organization_type}</Tag>
                  </div>
                )}
                {character.power_level !== undefined && character.power_level !== null && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('nivelDePoder')}</Text>
                    <Tag color={character.power_level >= 70 ? 'red' : character.power_level >= 50 ? 'orange' : 'default'}>
                      {character.power_level}
                    </Tag>
                  </div>
                )}
                {character.location && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('localizacao')}</Text>
                    <Text
                      style={{ flex: 1, minWidth: 0 }}
                      ellipsis={{ tooltip: character.location }}
                    >
                      {character.location}
                    </Text>
                  </div>
                )}
                {character.color && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('corRepresentativa')}</Text>
                    <Text style={{ flex: 1, minWidth: 0 }}>{character.color}</Text>
                  </div>
                )}
                {character.motto && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('lema')}</Text>
                    <Text
                      style={{ flex: 1, minWidth: 0 }}
                      ellipsis={{ tooltip: character.motto }}
                    >
                      {character.motto}
                    </Text>
                  </div>
                )}
                {character.organization_purpose && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('proposito')}</Text>
                    <Text
                      style={{ flex: 1, minWidth: 0 }}
                      ellipsis={{ tooltip: character.organization_purpose }}
                    >
                      {character.organization_purpose}
                    </Text>
                  </div>
                )}
                {character.organization_members && (
                  <div style={{ marginBottom: 8, display: 'flex', alignItems: 'flex-start' }}>
                    <Text type="secondary" style={{ flexShrink: 0 }}>{t('membros')}</Text>
                    <Text style={{ flex: 1, minWidth: 0, fontSize: 12, lineHeight: 1.6, wordBreak: 'break-all' }}>
                      {typeof character.organization_members === 'string'
                        ? character.organization_members
                        : JSON.stringify(character.organization_members)}
                    </Text>
                  </div>
                )}
              </>
            )}

            {/* 通用字段 - 背景信息截断显示 */}
            {character.background && (
              <div style={{ marginTop: 12 }}>
                <Paragraph
                  type="secondary"
                  style={{ fontSize: 12, marginBottom: 0 }}
                  ellipsis={{ tooltip: character.background, rows: 3 }}
                >
                  {character.background}
                </Paragraph>
              </div>
            )}
          </div>
        }
      />
    </Card>
  );
};
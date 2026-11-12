import { Modal, Form, Input, InputNumber, Select, Tag, Space, Button, message, Divider } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState, useEffect, useCallback } from 'react';
import type { ExpansionPlanData, Character } from '../types';
import { characterApi } from '../services/api';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;

interface ExpansionPlanEditorProps {
  visible: boolean;
  planData: ExpansionPlanData | null;
  chapterSummary: string | null;
  projectId: string;
  onSave: (data: ExpansionPlanData & { summary?: string }) => Promise<void>;
  onCancel: () => void;
}

export default function ExpansionPlanEditor({
  visible,
  planData,
  chapterSummary,
  projectId,
  onSave,
  onCancel
}: ExpansionPlanEditorProps) {
  const { t } = useTranslation('expansionPlanEditor');
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  
  // 关键事件标签输入
  const [keyEventInput, setKeyEventInput] = useState('');
  const [keyEvents, setKeyEvents] = useState<string[]>([]);
  
  // 角色列表和选择
  const [availableCharacters, setAvailableCharacters] = useState<Character[]>([]);
  const [characters, setCharacters] = useState<string[]>([]);
  const [loadingCharacters, setLoadingCharacters] = useState(false);

  // 加载项目角色列表
  const loadCharacters = useCallback(async () => {
    try {
      setLoadingCharacters(true);
      setAvailableCharacters([]); // 重置为空数组
      const response = await characterApi.getCharacters(projectId);
      console.log('Dados de personagens carregados:', response);
      
      // API返回的是 {total, items} 格式,需要提取items
      let chars: Character[] = [];
      if (Array.isArray(response)) {
        chars = response;
      } else if (response && typeof response === 'object' && 'items' in response) {
        const responseObj = response as { items?: Character[] };
        if (Array.isArray(responseObj.items)) {
          chars = responseObj.items;
        }
      } else {
        console.error('Formato de retorno da API de personagens inesperado:', response);
        message.warning(t('formatoDadosPersonagensInesperado'));
      }
      
      setAvailableCharacters(chars);
      console.log('Lista de personagens definida:', chars);
    } catch (error: unknown) {
      console.error('Falha ao carregar a lista de personagens:', error);
      setAvailableCharacters([]);
      const err = error as Error;
      message.error(t('falhaCarregarListaPersonagens') + (err?.message || t('erroDesconhecido')));
    } finally {
      setLoadingCharacters(false);
    }
  }, [projectId, t]);

  useEffect(() => {
    if (visible && projectId) {
      loadCharacters();
    }
  }, [visible, projectId, loadCharacters]);

  // 当planData或chapterSummary变化时更新状态
  useEffect(() => {
    if (visible) {
      if (planData) {
        setKeyEvents(planData.key_events || []);
        setCharacters(planData.character_focus || []);
        form.setFieldsValue({
          summary: chapterSummary || '',
          emotional_tone: planData.emotional_tone,
          narrative_goal: planData.narrative_goal,
          conflict_type: planData.conflict_type,
          estimated_words: planData.estimated_words
        });
      } else {
        // 重置状态
        setKeyEvents([]);
        setCharacters([]);
        form.setFieldsValue({
          summary: chapterSummary || ''
        });
      }
    }
  }, [planData, chapterSummary, form, visible]);

  const handleAddKeyEvent = () => {
    if (keyEventInput.trim()) {
      setKeyEvents([...keyEvents, keyEventInput.trim()]);
      setKeyEventInput('');
    }
  };

  const handleAddCharacter = (characterName: string) => {
    if (characterName && !characters.includes(characterName)) {
      setCharacters([...characters, characterName]);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      // 验证至少有一个关键事件
      if (keyEvents.length === 0) {
        message.warning(t('adicionePeloMenosEvento'));
        setLoading(false);
        return;
      }
      
      // 验证至少有一个角色
      if (characters.length === 0) {
        message.warning(t('adicionePeloMenosPersonagem'));
        setLoading(false);
        return;
      }
      
      const updatedPlan: ExpansionPlanData & { summary?: string } = {
        summary: values.summary,
        key_events: keyEvents,
        character_focus: characters,
        emotional_tone: values.emotional_tone,
        narrative_goal: values.narrative_goal,
        conflict_type: values.conflict_type,
        estimated_words: values.estimated_words,
        scenes: planData?.scenes || null
      };
      
      await onSave(updatedPlan);
      // message.success('规划信息保存成功');
    } catch (error) {
      console.error('Falha ao salvar:', error);
      message.error(t('falhaSalvarTenteNovamente'));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setKeyEvents([]);
    setCharacters([]);
    setKeyEventInput('');
    onCancel();
  };

  return (
    <Modal
      title={t('editarPlanejamentoCapitulo')}
      open={visible}
      onCancel={handleCancel}
      width={700}
      centered
      footer={[
        <Button key="cancel" onClick={handleCancel} disabled={loading}>
          {t('cancelar')}
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {t('salvar')}
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          emotional_tone: t('tensoEIntenso'),
          conflict_type: t('conflitoEntrePersonagens'),
          estimated_words: 3000
        }}
      >
        {/* 情节概要 */}
        <Form.Item
          label={t('resumoDaTrama')}
          name="summary"
          tooltip={t('descrevaBrevementeTramaPrincipal')}
        >
          <TextArea
            rows={3}
            placeholder={t('descrevaBrevementeTramaPrincipalCapitulo')}
            maxLength={500}
            showCount
          />
        </Form.Item>

        <Divider orientation="left">{t('planejamentoDetalhado')}</Divider>

        {/* 关键事件 */}
        <Form.Item
          label={t('eventosChave')}
          tooltip={t('adicionePeloMenosEvento')}
          required
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                placeholder={t('digiteEventoChavePressione')}
                value={keyEventInput}
                onChange={(e) => setKeyEventInput(e.target.value)}
                onPressEnter={handleAddKeyEvent}
              />
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAddKeyEvent}
              >
                {t('adicionar')}
              </Button>
            </Space.Compact>
            <Space wrap>
              {keyEvents.map((event, idx) => (
                <Tag
                  key={idx}
                  closable
                  onClose={(e) => {
                    e.preventDefault();
                    setKeyEvents(keyEvents.filter((_, i) => i !== idx));
                  }}
                  color="purple"
                  style={{ marginBottom: 8 }}
                >
                  <span style={{ fontWeight: 'bold', marginRight: 4 }}>#{idx + 1}</span>
                  {event}
                </Tag>
              ))}
            </Space>
          </Space>
        </Form.Item>

        {/* 涉及角色 */}
        <Form.Item
          label={t('personagensEnvolvidos')}
          tooltip={t('escolhaEntrePersonagensExistentes')}
          required
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Select
              placeholder={t('selecionarPersonagem')}
              style={{ width: '100%' }}
              loading={loadingCharacters}
              onChange={handleAddCharacter}
              value={undefined}
              showSearch
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={Array.isArray(availableCharacters)
                ? availableCharacters
                    .filter(char => !characters.includes(char.name))
                    .map(char => ({
                      label: char.name,
                      value: char.name,
                    }))
                : []}
              notFoundContent={
                loadingCharacters ? t('carregando') :
                !Array.isArray(availableCharacters) ? t('falhaCarregarPersonagens') :
                availableCharacters.length === 0 ? t('nenhumPersonagemCriePrimeiro') :
                t('todosPersonagensJaForam')
              }
            />
            <Space wrap>
              {characters.map((char, idx) => (
                <Tag
                  key={idx}
                  closable
                  onClose={() => setCharacters(characters.filter((_, i) => i !== idx))}
                  color="cyan"
                >
                  {char}
                </Tag>
              ))}
            </Space>
          </Space>
        </Form.Item>

        {/* 情感基调 */}
        <Form.Item
          label={t('tomEmocional')}
          name="emotional_tone"
          rules={[{ required: true, message: t('informeTomEmocional') }]}
          tooltip={t('exemploTensoIntensoComovente')}
        >
          <Input
            placeholder={t('informeTomEmocionalExemplo')}
            maxLength={20}
          />
        </Form.Item>

        {/* 冲突类型 */}
        <Form.Item
          label={t('tipoDeConflito')}
          name="conflict_type"
          rules={[{ required: true, message: t('informeTipoConflito') }]}
          tooltip={t('exemploConflitoEntrePersonagens')}
        >
          <Input
            placeholder={t('informeTipoConflitoExemplo')}
            maxLength={20}
          />
        </Form.Item>

        {/* 预估字数 */}
        <Form.Item
          label={t('palavrasEstimadas')}
          name="estimated_words"
          rules={[{ required: true, message: t('informeQuantidadeEstimadaPalavras') }]}
        >
          <InputNumber
            min={500}
            max={10000}
            step={100}
            style={{ width: '100%' }}
            formatter={(value) => t('palavras', { value })}
            parser={(value) => Number(value?.replace(/\D/g, '')) as 500 | 10000}
          />
        </Form.Item>

        {/* 叙事目标 */}
        <Form.Item
          label={t('objetivoNarrativo')}
          name="narrative_goal"
          rules={[{ required: true, message: t('informeObjetivoNarrativo') }]}
        >
          <TextArea
            rows={3}
            placeholder={t('descrevaObjetivoNarrativoCapitulo')}
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
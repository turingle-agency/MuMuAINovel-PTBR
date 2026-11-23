import api from './api';
import type {
  BriefDetail, BriefItem, BudgetView, Page, PageParams, RadarSettingsView, ResearchAccepted,
  ResearchDetail, ResearchFilters, ResearchListItem, ResearchRequest, SettingsPatch, SourceCheck, SourceName,
} from '../types/radar';

const base = '/radar';

export const radarApi = {
  settings: (signal?: AbortSignal) => api.get<unknown, RadarSettingsView>(`${base}/settings`, { signal }),
  saveSettings: (payload: SettingsPatch) => api.put<unknown, RadarSettingsView>(`${base}/settings`, payload),
  budget: (signal?: AbortSignal) => api.get<unknown, BudgetView>(`${base}/budget`, { signal }),
  checkSource: (source: SourceName) => api.post<unknown, SourceCheck>(`${base}/sources/${source}/check`),
  submit: (payload: ResearchRequest) => api.post<unknown, ResearchAccepted>(`${base}/researches`, payload),
  researches: (params: ResearchFilters, signal?: AbortSignal) =>
    api.get<unknown, Page<ResearchListItem>>(`${base}/researches`, { params, signal }),
  detail: (id: string, signal?: AbortSignal) =>
    api.get<unknown, ResearchDetail>(`${base}/researches/${encodeURIComponent(id)}`, { signal }),
  history: (id: string, params: PageParams, signal?: AbortSignal) =>
    api.get<unknown, Page<ResearchListItem>>(`${base}/researches/${encodeURIComponent(id)}/history`, { params, signal }),
  createBrief: (id: string) =>
    api.post<unknown, BriefDetail>(`${base}/researches/${encodeURIComponent(id)}/brief`),
  briefs: (params: PageParams, signal?: AbortSignal) =>
    api.get<unknown, Page<BriefItem>>(`${base}/briefs`, { params, signal }),
  brief: (id: string, signal?: AbortSignal) =>
    api.get<unknown, BriefDetail>(`${base}/briefs/${encodeURIComponent(id)}`, { signal }),
};

import type { ResearchDetail, ResearchStatus } from '../types/radar';

export function shouldPoll(status: ResearchStatus): boolean {
  return status === 'pending' || status === 'running';
}

export function canCreateBrief(
  research: Pick<ResearchDetail, 'status' | 'citable_count' | 'legacy'>,
): boolean {
  return !research.legacy && research.citable_count > 0 &&
    (research.status === 'complete' || research.status === 'partial');
}

export function money(value: string | number, currency: string): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(Number(value));
}

export function dateTime(value: string | null): string {
  return value ? new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—';
}

export function calendarDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(new Date(value)) : '—';
}

export function number(value: number | null): string {
  return value === null ? '—' : new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(value);
}

export function safeLink(value: string | null): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    if (['https:', 'http:'].includes(url.protocol) && !url.username && !url.password) return url.href;
  } catch {
    return undefined;
  }
}

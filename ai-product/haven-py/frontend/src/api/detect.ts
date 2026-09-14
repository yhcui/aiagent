import { api } from './client';

/** 分段标签：0 = 人工，1 = AI，2 = 疑似 AI */
export type SegmentLabelType = 0 | 1 | 2;

export interface DetectSegment {
  text: string;
  label: SegmentLabelType;
  conf: number;
  order: number;
  position: [number, number];
}

export interface DetectResult {
  status: string;
  /** 整体置信度，越大越可能命中风险内容 */
  softmax_confidence: number;
  /** 整体疑似风险内容占比 */
  ratio_confidence: number;
  /** 各类型内容占比：'0' 人工 / '1' AI / '2' 疑似 AI，取值 [0, 1] */
  labels_ratio: Record<'0' | '1' | '2', number>;
  segment_labels: DetectSegment[];
  /** 朱雀模型自身用量（与免费额度核算无关） */
  usage: { total_tokens: number };
  /** 本次调用实际扣减的 Makers 免费额度 token 数 */
  makers_models_usage: { total_tokens: number };
  msg: string;
}

export const detectText = (text: string, isMerge: boolean) =>
  api.post<DetectResult>('/detect', { text, is_merge: isMerge });

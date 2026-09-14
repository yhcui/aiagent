import { useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { detectText, type DetectResult, type SegmentLabelType } from '../api/detect';
import { ApiError } from '../api/client';

const MAX_LEN = 5000;

const VERDICTS: Record<SegmentLabelType, { label: string; icon: string; cls: string }> = {
  0: { label: '人工撰写', icon: '✍️', cls: 'human' },
  1: { label: 'AI 生成', icon: '🤖', cls: 'ai' },
  2: { label: '疑似 AI', icon: '🔎', cls: 'suspect' },
};

function verdictOf(result: DetectResult) {
  const r = result.labels_ratio;
  const key = (['0', '1', '2'] as const).reduce((a, b) => (r[a] >= r[b] ? a : b));
  return VERDICTS[Number(key) as SegmentLabelType];
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export default function DetectPage() {
  const [text, setText] = useState('');
  const [isMerge, setIsMerge] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<DetectResult | null>(null);
  const [error, setError] = useState('');

  const stars = useMemo(
    () =>
      Array.from({ length: 25 }, () => ({
        top: Math.random() * 50,
        left: Math.random() * 100,
        size: Math.random() * 2 + 1,
        delay: Math.random() * 4,
      })),
    []
  );

  const handleDetect = async () => {
    const content = text.trim();
    if (!content || busy) return;
    setBusy(true);
    setError('');
    try {
      const data = await detectText(content, isMerge);
      setResult(data);
    } catch (e) {
      setResult(null);
      if (e instanceof ApiError) {
        setError(e.status === 401 ? '登录已失效，请重新登录' : e.message);
      } else {
        console.error('检测失败', e);
        setError('检测失败，请稍后重试');
      }
    } finally {
      setBusy(false);
    }
  };

  const verdict = result ? verdictOf(result) : null;
  const segments = result?.segment_labels ?? [];
  const showSegments = !isMerge && segments.length > 1;

  return (
    <div className="detect-page">
      {stars.map((s, i) => (
        <span
          key={`s-${i}`}
          className="ideas-star"
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: s.size,
            height: s.size,
            animationDelay: `${s.delay}s`,
          }}
        />
      ))}

      <div className="ideas-fire-glow" />

      <div className="detect-board">
        <h1 className="ideas-title">
          <span className="flame">🔍</span>
          AI 鉴真
        </h1>
        <p className="ideas-subtitle">借一簇火光，辨人语与机鸣</p>

        <div className="detect-textarea-wrap">
          <textarea
            className="detect-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="把想鉴别的文字贴到这张纸上…"
            disabled={busy}
            maxLength={MAX_LEN}
            rows={8}
          />
        </div>

        <div className="detect-controls">
          <label className="detect-merge-toggle" title="合并段落时输出整体判断；否则每个段落独立判断">
            <input
              type="checkbox"
              checked={isMerge}
              onChange={(e) => setIsMerge(e.target.checked)}
              disabled={busy}
            />
            <span className="detect-toggle-track">
              <span className="detect-toggle-thumb" />
            </span>
            合并段落整体判断
          </label>

          <span className="detect-count">
            {text.length}/{MAX_LEN}
          </span>

          <button
            className="detect-submit-btn"
            onClick={handleDetect}
            disabled={busy || !text.trim()}
          >
            {busy ? '鉴别中…' : '点火鉴别'}
          </button>
        </div>

        {error && <div className="login-error">{error}</div>}

        <AnimatePresence mode="wait">
          {result && verdict ? (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20, rotate: -1.5 }}
              animate={{ opacity: 1, y: 0, rotate: -0.4 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3, type: 'spring', stiffness: 120 }}
              className="detect-result"
            >
              <div className="idea-pin" />

              <div className={`detect-verdict ${verdict.cls}`}>
                <span className="detect-verdict-icon">{verdict.icon}</span>
                <span className="detect-verdict-label">{verdict.label}</span>
                <span className="detect-verdict-conf">
                  置信度 {pct(result.softmax_confidence)}
                </span>
              </div>

              <div className="detect-bars">
                {(['0', '1', '2'] as const).map((k) => {
                  const v = result.labels_ratio[k];
                  const meta = VERDICTS[Number(k) as SegmentLabelType];
                  return (
                    <div key={k} className="detect-bar-row">
                      <span className="detect-bar-name">{meta.label}</span>
                      <div className="detect-bar">
                        <div
                          className={`detect-bar-fill ${meta.cls}`}
                          style={{ width: `${Math.max(v * 100, v > 0 ? 2 : 0)}%` }}
                        />
                      </div>
                      <span className="detect-bar-pct">{pct(v)}</span>
                    </div>
                  );
                })}
              </div>

              {showSegments && (
                <div className="detect-segments">
                  {segments.map((seg) => {
                    const meta = VERDICTS[seg.label];
                    return (
                      <div key={seg.order} className="detect-segment">
                        <div className="detect-segment-head">
                          <span className={`detect-chip ${meta.cls}`}>
                            {meta.icon} {meta.label}
                          </span>
                          <span className="detect-segment-conf">{pct(seg.conf)}</span>
                        </div>
                        <p className="detect-segment-text">{seg.text}</p>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="detect-meta">
                本次消耗 {result.makers_models_usage?.total_tokens ?? 0} token（计入免费额度）
              </div>
            </motion.div>
          ) : (
            !error && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="ideas-empty"
              >
                <span className="lantern">🪔</span>
                <p style={{ marginTop: 16, fontSize: 17, fontWeight: 600 }}>
                  火光已备好，等一段文字
                </p>
                <p style={{ marginTop: 4, fontSize: 13, opacity: 0.6 }}>
                  贴上内容，看看它出自人手还是 AI
                </p>
              </motion.div>
            )
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useState } from 'react'
import SignPlayer from './SignPlayer.jsx'
import { engines as fetchEngines, randomJoke, translate } from './api.js'

const EXAMPLES = ['今天天气很好', '我想和朋友去医院', '谢谢你的帮助', '明天上午八点开会']

const STATUS_TEXT = {
  matched: '已匹配',
  partial: '部分匹配（只找到部分单字）',
  missing: '词库里没有这个词',
}

// 引擎选择记在本地，刷新后还是上次那个
const ENGINE_KEY = 'signEngine'
const ENGINE_NAME = { local: 'jieba', doubao: '豆包' }

const DEFAULT_ENGINES = [
  { id: 'local', name: '本地分词（jieba）', available: true },
  { id: 'doubao', name: '豆包大模型', available: false, reason: '正在检查配置…' },
]

export default function App() {
  const [text, setText] = useState('')
  const [reorder, setReorder] = useState(true)
  const [engine, setEngine] = useState(() => localStorage.getItem(ENGINE_KEY) || 'local')
  const [engineList, setEngineList] = useState(DEFAULT_ENGINES)
  const [result, setResult] = useState(null)
  const [current, setCurrent] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [jokeText, setJokeText] = useState('')

  const clips = result?.clips ?? []
  const doubaoInfo = engineList.find((it) => it.id === 'doubao') || {}

  const chooseEngine = (id) => {
    setEngine(id)
    try {
      localStorage.setItem(ENGINE_KEY, id)
    } catch (e) {}
  }

  // 问一下后端哪些引擎可用；本地存的那个现在不可用就落回 jieba
  useEffect(() => {
    fetchEngines()
      .then((data) => {
        const items = data.items?.length ? data.items : DEFAULT_ENGINES
        setEngineList(items)
        const picked = items.find((it) => it.id === engine)
        if (!picked || !picked.available) chooseEngine('local')
      })
      .catch(() => {
        setEngineList(DEFAULT_ENGINES.map((it) => (
          it.id === 'doubao' ? { ...it, reason: '拿不到引擎状态，后端可能没起' } : it
        )))
        chooseEngine('local')
      })
  }, [])

  // 当前播放到哪个词（用来高亮）
  const activeToken = useMemo(() => {
    if (!result) return -1
    return result.tokens.findIndex((t) => t.clipIndexes.includes(current))
  }, [result, current])

  const applyResult = (data) => {
    setResult(data)
    setCurrent(0)
  }

  const doTranslate = async (value = text, useEngine = engine) => {
    const input = (value ?? '').trim()
    if (!input) {
      setError('请先输入一句话')
      return
    }
    setLoading(true)
    setError('')
    try {
      applyResult(await translate(input, reorder, useEngine))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // 一键换引擎，把同一句话再翻一遍，方便对比两种效果
  const switchAndTranslate = (id) => {
    chooseEngine(id)
    doTranslate(result?.text || text, id)
  }

  const doJoke = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await randomJoke(reorder, engine)
      setJokeText(data.text)
      setText(data.text)
      applyResult(data.translation)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const clearAll = () => {
    setText('')
    setJokeText('')
    setResult(null)
    setCurrent(0)
    setError('')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>手语翻译</h1>
        <p>输入中文句子，用手语视频连续播放出来</p>
      </header>

      <section className="card">
        <textarea
          className="input"
          rows={3}
          value={text}
          placeholder="例如：今天天气很好，我想和朋友去医院"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) doTranslate()
          }}
        />

        <div className="toolbar">
          <button className="primary" onClick={() => doTranslate()} disabled={loading}>
            {loading ? '处理中…' : '翻译成手语'}
          </button>
          <button onClick={doJoke} disabled={loading}>讲个笑话</button>
          <button onClick={clearAll} disabled={loading}>清空</button>
          <label className="switch">
            <input
              type="checkbox"
              checked={reorder}
              disabled={engine === 'doubao'}
              onChange={(e) => setReorder(e.target.checked)}
            />
            按手语语序调整（时间在前、疑问在后）
            {engine === 'doubao' ? <span className="engine-hint">语序由模型决定</span> : null}
          </label>
        </div>

        <div className="engine-row">
          <span className="engine-label">分词方式</span>
          {engineList.map((it) => (
            <label
              key={it.id}
              className={'engine-opt' + (engine === it.id ? ' on' : '') + (it.available ? '' : ' off')}
              title={it.available ? '' : it.reason || '当前不可用'}
            >
              <input
                type="radio"
                name="engine"
                value={it.id}
                checked={engine === it.id}
                disabled={!it.available || loading}
                onChange={() => chooseEngine(it.id)}
              />
              {it.name}
            </label>
          ))}
          {!doubaoInfo.available && doubaoInfo.reason ? (
            <span className="engine-hint">豆包不可用：{doubaoInfo.reason}</span>
          ) : null}
        </div>

        <div className="examples">
          试试：
          {EXAMPLES.map((ex) => (
            <button key={ex} className="chip" onClick={() => { setText(ex); doTranslate(ex) }}>{ex}</button>
          ))}
        </div>

        {error ? <div className="error">{error}</div> : null}
        {jokeText ? <div className="joke">笑话：{jokeText}</div> : null}
      </section>

      <section className="card">
        <SignPlayer clips={clips} currentIndex={current} onIndexChange={setCurrent} />
      </section>

      {result ? (
        <section className="card">
          <div className="result-head">
            <span>
              分词结果
              <span className={'engine-tag ' + result.engine}>
                {ENGINE_NAME[result.engine] || result.engine}
              </span>
            </span>
            <span className="coverage">
              命中率 {Math.round(result.coverage * 100)}% · 共 {clips.length} 个手语动作
            </span>
          </div>

          {result.fallbackReason ? (
            <div className="fallback">豆包这次没成功，已自动用 jieba 分词：{result.fallbackReason}</div>
          ) : null}

          {result.gloss?.length ? (
            <div className="gloss-row">手语语序（豆包给的）：{result.gloss.join(' · ')}</div>
          ) : null}

          <div className="re-translate">
            {(result.engine === 'doubao' ? ['local'] : ['doubao']).map((id) => (
              <button
                key={id}
                className="chip"
                disabled={loading || (id === 'doubao' && !doubaoInfo.available)}
                title={id === 'doubao' && !doubaoInfo.available ? doubaoInfo.reason || '' : ''}
                onClick={() => switchAndTranslate(id)}
              >
                改用 {ENGINE_NAME[id]} 重译
              </button>
            ))}
          </div>

          <div className="tokens">
            {result.tokens.map((t, i) => (
              <button
                key={i}
                className={`token ${t.status}` + (i === activeToken ? ' active' : '')}
                title={STATUS_TEXT[t.status] || ''}
                disabled={!t.clipIndexes.length}
                onClick={() => t.clipIndexes.length && setCurrent(t.clipIndexes[0])}
              >
                {t.token}
              </button>
            ))}
          </div>

          {result.missing.length ? (
            <div className="missing">词库里没有（或只能拆成单字）：{result.missing.join('、')}</div>
          ) : null}

          <div className="clip-list">
            {clips.map((c, i) => (
              <button
                key={i}
                className={'clip' + (i === current ? ' active' : '')}
                onClick={() => setCurrent(i)}
              >
                <span className="clip-index">{i + 1}</span>
                <span className="clip-word">{c.word}</span>
                <span className="clip-pinyin">{c.pinyin}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}

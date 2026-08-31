import React, { useEffect, useRef, useState } from 'react'

/**
 * 手语视频播放器：把一串视频按顺序播完，看起来就像拼接成了一句话。
 *
 * 两个 video 交替使用（双缓冲）：下一段先在隐藏的那块里加载好，
 * 等它有画面了再切换显示，避免换 src 时的黑闪。
 *
 * 每段视频自带「起手 / 收手」动作，连播时会一顿一顿的，所以做了裁剪：
 *   不是第一段  -> 从 trim 秒处开始播（跳过起手）
 *   不是最后一段 -> 播到 duration - trim 就切下一段（跳过收手）
 * 视频最短只有 1.2 秒，头尾都切会没剩多少，所以保证至少留 MIN_KEEP 秒，
 * 不够时按比例少切一点。
 */

const DEFAULT_TRIM = 0.5   // 头尾各裁掉多少秒
const MIN_KEEP = 0.5       // 一段视频至少要播这么久

export default function SignPlayer({ clips, currentIndex, onIndexChange }) {
  const slotA = useRef(null)
  const slotB = useRef(null)
  const slots = [slotA, slotB]
  // 两块屏各自装着哪一段、哪个视频、有没有准备好。
  // 必须连 video 一起记：重新翻译后 index 又从 0 开始，光看 index 会把上一批的旧视频当成已就绪
  const slotState = useRef([
    { index: -1, video: null, ready: false },
    { index: -1, video: null, ready: false },
  ])
  const pending = useRef([null, null])   // 某块屏准备好之后要做的事

  const [active, setActive] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [loop, setLoop] = useState(false)
  const [trim, setTrim] = useState(DEFAULT_TRIM)

  const activeRef = useRef(0)
  const playingRef = useRef(false)
  const speedRef = useRef(1)
  const loopRef = useRef(false)
  const trimRef = useRef(DEFAULT_TRIM)
  const clipsRef = useRef(clips)
  const indexRef = useRef(currentIndex)

  activeRef.current = active
  playingRef.current = playing
  speedRef.current = speed
  loopRef.current = loop
  trimRef.current = trim
  clipsRef.current = clips
  indexRef.current = currentIndex

  const total = clips.length
  const clip = clips[currentIndex]

  // ---------- 裁剪区间 ----------

  const clipRange = (duration, index) => {
    if (!duration || !isFinite(duration)) return { start: 0, end: duration || 0 }
    const t = trimRef.current
    let head = index <= 0 ? 0 : t
    let tail = index >= clipsRef.current.length - 1 ? 0 : t
    const room = Math.max(duration - MIN_KEEP, 0)
    if (head + tail > room) {
      const k = head + tail > 0 ? room / (head + tail) : 0
      head *= k
      tail *= k
    }
    return { start: head, end: duration - tail }
  }

  // ---------- 基础操作 ----------

  // ---------- 屏的状态 ----------

  /** 这块屏里装的是不是第 index 段（连视频地址一起对） */
  const slotHas = (slot, index) => {
    const st = slotState.current[slot]
    const target = clipsRef.current[index]
    return !!target && !!st && st.index === index && st.video === target.video
  }

  const setActiveSlot = (slot) => {
    activeRef.current = slot
    setActive(slot)
  }

  const startPlay = (el) => {
    if (!el) return
    el.playbackRate = speedRef.current
    el.play().catch(() => setPlaying(false))
  }

  const seekToStart = (el, index) => {
    if (!el) return
    const { start } = clipRange(el.duration, index)
    try { el.currentTime = start } catch (e) {}
  }

  /** 把某一段装进指定的屏里，装好（画面已就绪、已跳到起始点）后执行 onReady */
  const prepare = (slot, index, onReady) => {
    const el = slots[slot].current
    const target = clipsRef.current[index]
    if (!el || !target) return
    slotState.current[slot] = { index, video: target.video, ready: false }
    pending.current[slot] = onReady || null

    // 这块屏被别人抢去装其他段了，本次加载作废
    const stale = () => {
      const st = slotState.current[slot]
      return !st || st.index !== index || st.video !== target.video
    }

    const done = () => {
      if (stale()) return
      slotState.current[slot].ready = true
      const cb = pending.current[slot]
      pending.current[slot] = null
      if (cb) cb()
    }

    const onMeta = () => {
      if (stale()) return
      const { start } = clipRange(el.duration, index)
      if (start > 0.02) {
        // 先跳到起始点，跳完才算准备好，这样切过去就是裁剪后的第一帧
        el.addEventListener('seeked', done, { once: true })
        try { el.currentTime = start } catch (e) { done() }
      } else if (el.readyState >= 2) {
        done()
      } else {
        el.addEventListener('loadeddata', done, { once: true })
      }
    }

    el.addEventListener('loadedmetadata', onMeta, { once: true })
    el.src = target.video
    el.load()
  }

  const advance = () => {
    const i = indexRef.current
    if (i < clipsRef.current.length - 1) {
      onIndexChange(i + 1)
    } else if (loopRef.current) {
      onIndexChange(0)
    } else {
      setPlaying(false)
    }
  }

  // 到了「结尾裁剪点」就提前切下一段；cutRef 防止同一段被切两次
  const cutRef = useRef(-1)

  const cutIfNeeded = () => {
    const el = slots[activeRef.current].current
    if (!el || el.paused || !el.duration) return
    const { end } = clipRange(el.duration, indexRef.current)
    if (el.currentTime < end - 0.02) return
    if (cutRef.current === indexRef.current) return
    cutRef.current = indexRef.current
    el.pause()
    advance()
  }

  // ---------- 切段 ----------

  useEffect(() => {
    if (!clip) return
    cutRef.current = -1
    const cur = activeRef.current
    const other = 1 - cur
    const curEl = slots[cur].current
    const otherEl = slots[other].current
    if (!curEl || !otherEl) return

    // 正在显示的这块屏就装着要播的这段（首次加载 / 重播 / 手动点同一个词）
    if (slotHas(cur, currentIndex)) {
      seekToStart(curEl, currentIndex)
      if (playingRef.current) startPlay(curEl)
      return
    }

    // 这块屏装的不是要播的内容，先停下来，别让旧视频接着播
    curEl.pause()

    let cancelled = false
    let timer = 0

    const swap = () => {
      if (cancelled) return
      clearTimeout(timer)
      setActiveSlot(other)
      if (playingRef.current) startPlay(otherEl)
      curEl.pause()
    }

    const st = slotState.current[other]
    if (slotHas(other, currentIndex) && st.ready) {
      swap()                       // 已经预加载好了，直接切
    } else if (slotHas(other, currentIndex)) {
      pending.current[other] = swap // 还在加载，等它好了再切
      timer = setTimeout(swap, 2000)
    } else {
      prepare(other, currentIndex, swap)
      timer = setTimeout(swap, 2000)   // 网络慢时兜底，别卡住不动
    }

    return () => {
      cancelled = true
      clearTimeout(timer)
      if (pending.current[other] === swap) pending.current[other] = null
    }
  }, [clip?.video, currentIndex, clips])

  // 预加载下一段到隐藏的那块屏
  useEffect(() => {
    const other = 1 - active
    const nextIndex = currentIndex + 1 < clips.length ? currentIndex + 1 : (loop ? 0 : -1)
    if (nextIndex < 0 || !clips[nextIndex]) return
    if (slotState.current[other].index === currentIndex) return  // 这块屏正在为当前段做准备，别动它
    if (slotHas(other, nextIndex)) return
    prepare(other, nextIndex)
  }, [active, currentIndex, clips, loop])

  // 播到「结尾裁剪点」就提前切下一段。
  // rAF 在前台最精准，但标签页切到后台会被降频，所以视频的 timeupdate 也会兜一次。
  useEffect(() => {
    if (!playing) return
    let raf = 0
    const tick = () => {
      cutIfNeeded()
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [playing, active, currentIndex, clips])

  // 播放 / 暂停
  useEffect(() => {
    const el = slots[active].current
    if (!el) return
    if (playing) {
      // 这块屏里还是上一批的视频（新结果刚进来、还没切过去），等 swap 完再播
      if (!slotHas(active, indexRef.current)) return
      if (cutRef.current === indexRef.current) cutRef.current = -1
      startPlay(el)
    } else {
      el.pause()
    }
  }, [playing, active])

  // 新的翻译结果进来后自动从头播放
  useEffect(() => {
    if (clips.length) setPlaying(true)
  }, [clips])

  useEffect(() => {
    const el = slots[active].current
    if (el) el.playbackRate = speed
  }, [speed, active])

  // ---------- 控件 ----------

  const handleEnded = (slot) => {
    if (slot !== activeRef.current) return
    advance()
  }

  const play = () => setPlaying(true)
  const pause = () => setPlaying(false)

  const replay = () => {
    setPlaying(true)
    if (currentIndex !== 0) {
      onIndexChange(0)
    } else {
      const el = slots[activeRef.current].current
      seekToStart(el, 0)
      startPlay(el)
    }
  }

  const step = (delta) => {
    const target = Math.min(Math.max(currentIndex + delta, 0), total - 1)
    onIndexChange(target)
  }

  if (!total) {
    return (
      <div className="player empty">
        <div className="player-placeholder">输入句子后点击「翻译成手语」，这里会连续播放手语视频</div>
      </div>
    )
  }

  return (
    <div className="player">
      <div className="video-wrap">
        {[0, 1].map((slot) => (
          <video
            key={slot}
            ref={slots[slot]}
            className={'video' + (active === slot ? ' show' : '')}
            playsInline
            muted
            preload="auto"
            onEnded={() => handleEnded(slot)}
            onTimeUpdate={() => { if (slot === activeRef.current) cutIfNeeded() }}
            onClick={() => (playing ? pause() : play())}
          />
        ))}
        <div className="video-caption">
          <span className="caption-word">{clip?.word}</span>
          {clip?.pinyin ? <span className="caption-pinyin">{clip.pinyin}</span> : null}
        </div>
      </div>

      <div className="progress">
        {clips.map((c, i) => (
          <span
            key={i}
            className={'progress-dot' + (i === currentIndex ? ' active' : i < currentIndex ? ' done' : '')}
            title={c.word}
            onClick={() => onIndexChange(i)}
          />
        ))}
      </div>

      <div className="controls">
        <button onClick={() => step(-1)} disabled={currentIndex === 0}>上一个</button>
        {playing ? <button className="primary" onClick={pause}>暂停</button> : <button className="primary" onClick={play}>播放</button>}
        <button onClick={() => step(1)} disabled={currentIndex >= total - 1}>下一个</button>
        <button onClick={replay}>重播</button>
        <span className="counter">{currentIndex + 1} / {total}</span>
        <label className="speed">
          速度
          <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
            <option value={0.5}>0.5x</option>
            <option value={0.75}>0.75x</option>
            <option value={1}>1x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
          </select>
        </label>
        <label className="loop">
          <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} />
          循环
        </label>
      </div>

      <div className="trim-row">
        <label className="trim">
          头尾裁剪
          <input
            type="range"
            min="0"
            max="0.9"
            step="0.05"
            value={trim}
            onChange={(e) => setTrim(Number(e.target.value))}
          />
          <span className="trim-value">{trim.toFixed(2)}s</span>
        </label>
        <span className="trim-hint">
          第一段保留起手、最后一段保留收手；视频太短时会少裁一点，至少播 {MIN_KEEP}s
        </span>
      </div>
    </div>
  )
}

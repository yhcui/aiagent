const BASE = ''

async function request(url, options) {
  const res = await fetch(BASE + url, options)
  if (!res.ok) {
    let msg = `请求失败 (${res.status})`
    try {
      const data = await res.json()
      if (data.detail) msg = data.detail
    } catch (e) {}
    throw new Error(msg)
  }
  return res.json()
}

export function translate(text, reorder = true, engine = 'local') {
  return request('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, reorder, engine }),
  })
}

export function randomJoke(reorder = true, engine = 'local') {
  return request(`/api/joke?reorder=${reorder}&engine=${engine}`)
}

export function engines() {
  return request('/api/engines')
}

export function health() {
  return request('/api/health')
}

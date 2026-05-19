const BASE = '/api'

export async function get(url) {
  const res = await fetch(BASE + url)
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

export async function post(url, body) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

export async function postForm(url, formData) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

export async function del(url) {
  const res = await fetch(BASE + url, { method: 'DELETE' })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText)
  return res.json()
}

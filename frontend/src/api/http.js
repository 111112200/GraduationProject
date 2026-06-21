const BASE = '/api'

function getHeaders(customHeaders = {}) {
  const token = localStorage.getItem('token')
  const headers = { ...customHeaders }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function handleResponse(res) {
  if (res.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '#/login' // Or whatever routing mechanism is used
    throw new Error('未授权，请重新登录')
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || res.statusText)
  }
  return res.json()
}

export async function get(url) {
  const res = await fetch(BASE + url, {
    headers: getHeaders()
  })
  return handleResponse(res)
}

export async function post(url, body) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body),
  })
  return handleResponse(res)
}

export async function postForm(url, formData) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: getHeaders(),
    body: formData,
  })
  return handleResponse(res)
}

export async function del(url) {
  const res = await fetch(BASE + url, { 
    method: 'DELETE',
    headers: getHeaders()
  })
  return handleResponse(res)
}

// Special case for login which returns form data response
export async function postUrlEncoded(url, formData) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  })
  return handleResponse(res)
}

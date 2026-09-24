export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('flowinbox_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    credentials: 'include',
    ...options,
    headers,
  };

  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  try {
    const res = await fetch(`${API_BASE}${formattedEndpoint}`, config);

    if (!res.ok) {
      let errorDetail = res.statusText;
      try {
        const errorData = await res.json();
        errorDetail = errorData.detail || JSON.stringify(errorData);
      } catch (e) {
        // use status text
      }
      throw new Error(`API Error (${res.status}): ${errorDetail}`);
    }

    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    console.error(`[API Client Error] ${endpoint}:`, err);
    throw err;
  }
}

function buildUrl(endpoint, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null) {
      query.append(key, val);
    }
  });
  const queryString = query.toString();
  return queryString ? `${endpoint}?${queryString}` : endpoint;
}

export const api = {
  get: (endpoint, params = {}) => {
    return request(buildUrl(endpoint, params), { method: 'GET' });
  },

  post: (endpoint, body, opts = {}) => {
    const params = opts && opts.params ? opts.params : (opts && !opts.params && typeof opts === 'object' && !Array.isArray(opts) ? opts : {});
    const url = (opts && opts.params) ? buildUrl(endpoint, opts.params) : (typeof opts === 'object' && Object.keys(opts).length > 0 && !opts.headers ? buildUrl(endpoint, opts) : endpoint);
    return request(url, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      ...opts,
    });
  },

  put: (endpoint, body, opts = {}) => {
    const url = (opts && opts.params) ? buildUrl(endpoint, opts.params) : endpoint;
    return request(url, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
      ...opts,
    });
  },

  delete: (endpoint, opts = {}) => {
    const url = (opts && opts.params) ? buildUrl(endpoint, opts.params) : endpoint;
    return request(url, {
      method: 'DELETE',
      ...opts,
    });
  },
};

export default api;

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: `${API_BASE}/api` })

// Auto-attach JWT token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    return Promise.reject(err)
  }
)

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
}

// Chatbot API
export const chatAPI = {
  sendMessage: (message, history) => api.post('/chat/message', { message, history }),
}

// Diet API
export const dietAPI = {
  generatePlan: (profile) => api.post('/diet/generate-plan', profile),
  logMeal: (data) => api.post('/diet/log-meal', data),
  getAdherence: () => api.get('/diet/adherence'),
}

// Reports API
export const reportsAPI = {
  uploadReport: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/reports/upload', fd)
  },
  getReports: () => api.get('/reports/my-reports'),
}

// Symptoms API
export const symptomsAPI = {
  logSymptoms: (data) => api.post('/symptoms/log', data),
  getTrends: (days) => api.get(`/symptoms/trends?days=${days}`),
}

// Medications API
export const medsAPI = {
  add: (data) => api.post('/medications/add', data),
  list: () => api.get('/medications/list'),
  update: (id, data) => api.put(`/medications/${id}`, data),
  delete: (id) => api.delete(`/medications/${id}`),
}

// Clinical Trials API
export const trialsAPI = {
  searchTrials: (cancerType) => api.get(`/trials/search?cancer_type=${cancerType}`),
  getReferences: () => api.get('/trials/references'),
}

// Caregiver API
export const caregiverAPI = {
  link: (email) => api.post('/caregiver/link', { patient_email: email }),
  getSummary: () => api.get('/caregiver/patient-summary'),
  logMeal: (data) => api.post('/caregiver/log-meal', data),
  logMedication: (medicationId) => api.post('/caregiver/log-medication', { medication_id: medicationId }),
}

export default api

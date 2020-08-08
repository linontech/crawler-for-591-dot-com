import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  // timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
  }
})

// Request Interceptor
api.interceptors.request.use(function (config) {
  config.headers['Authorization'] = 'Fake Token'
  return config
})

// Response Interceptor to handle and log errors
api.interceptors.response.use(function (response) {
  return response
}, function (error) {
  // Handle Error
  console.log(error)
  return Promise.reject(error)
})

export default {
  startCrawling () {
    return api.post('start')
      .then(response => response.data)
  },
  stopCrawling () {
    return api.post('stop')
      .then(response => response.data)
  },
  queryRecords (payload) {
    return api.post('search', payload)
      .then(response => response.data)
  }
}

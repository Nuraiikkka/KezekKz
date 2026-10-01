import client from './client.js'

export const getClinics = () => client.get('/clinics/').then((r) => r.data)

export const getClinic = (slug) => client.get(`/clinics/${slug}/`).then((r) => r.data)

export const getSpecialties = (slug) => client.get(`/clinics/${slug}/specialties/`).then((r) => r.data)

export const getSlots = (slug, params) => client.get(`/clinics/${slug}/slots/`, { params }).then((r) => r.data)

export const getQuestions = () => client.get('/intake/questions/').then((r) => r.data)

export const submitIntake = (clinic, answers) => client.post('/intake/', { clinic, answers }).then((r) => r.data)

export const createAppointment = (payload) => client.post('/appointments/', payload).then((r) => r.data)

export const trackAppointment = (token) => client.get(`/appointments/track/${token}/`).then((r) => r.data)

export const cancelAppointment = (token) => client.post(`/appointments/track/${token}/cancel/`).then((r) => r.data)

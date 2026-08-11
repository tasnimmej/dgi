import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [companyIce, setCompanyIce] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await axios.post('http://127.0.0.1:8000/auth/register', {
        email,
        password,
        company_ice: companyIce,
        company_name: companyName
      })
      navigate('/login')
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Erreur lors de l\'inscription')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-md mx-auto bg-white rounded-xl shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Créer un compte</h1>
        {error && <div className="mb-3 text-red-600">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full p-2 border rounded mb-3" />

          <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full p-2 border rounded mb-3" />

          <label className="block text-sm font-medium text-gray-700">ICE de la société (optionnel)</label>
          <input value={companyIce} onChange={e => setCompanyIce(e.target.value)} className="w-full p-2 border rounded mb-3" />

          <label className="block text-sm font-medium text-gray-700">Nom de la société (optionnel)</label>
          <input value={companyName} onChange={e => setCompanyName(e.target.value)} className="w-full p-2 border rounded mb-4" />

          <button className="w-full bg-blue-700 text-white p-2 rounded" disabled={loading}>{loading ? 'Création...' : 'Créer le compte'}</button>
        </form>

        <div className="mt-4 text-sm text-center">
          <a href="/login" className="text-blue-600">Vous avez déjà un compte ?</a>
        </div>
      </div>
    </div>
  )
}

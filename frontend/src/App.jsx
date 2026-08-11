import { useState, useEffect } from 'react'
import axios from 'axios'
import { Routes, Route, Link } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import UploadInvoice from './pages/UploadInvoice'
import { getToken, removeToken } from './utils/auth'

function App() {
  // États existants
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  // Nouvel état pour l'historique
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Fonction pour charger l'historique depuis l'API
  const fetchHistory = async () => {
    setLoadingHistory(true)
    try {
      const response = await axios.get('http://127.0.0.1:8000/declarations', {
        headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {}
      })
      setHistory(response.data)
    } catch (err) {
      console.error("Erreur lors du chargement de l'historique", err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Charger l'historique au démarrage de l'app
  useEffect(() => {
    fetchHistory()
  }, [])

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setResult(null)
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) {
      alert("Veuillez sélectionner un fichier CSV !")
      return
    }

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('http://127.0.0.1:8000/upload-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data', ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) }
      })
      setResult(response.data)
      // Recharger l'historique après un import réussi
      fetchHistory()
    } catch (err) {
      console.error(err)
      setError("Erreur lors de l'import. Vérifiez le format de votre CSV.")
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    removeToken()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-blue-900">📊 Assistant Déclaration DGI</h1>
          <nav className="flex gap-3">
            <Link to="/">Dashboard</Link>
        <Link to="/upload-invoice" className="text-sm bg-blue-50 px-3 py-1 rounded">Téléverser facture</Link>
        {getToken() ? (
          <button onClick={handleLogout} className="text-sm bg-red-100 px-3 py-1 rounded">Se déconnecter</button>
        ) : (
          <>
            <Link to="/login" className="text-sm bg-blue-100 px-3 py-1 rounded">Connexion</Link>
            <Link to="/register" className="text-sm bg-gray-100 px-3 py-1 rounded">Inscription</Link>
          </>
        )}
          </nav>
        </header>

        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/upload-invoice" element={<UploadInvoice />} />

          <Route path="/" element={(
            <>
              {/* --- PARTIE IMPORT --- */}
        <div className="bg-white shadow-xl rounded-2xl p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Importer un mois</h2>
          <div className="border-2 border-dashed border-blue-300 rounded-xl p-6 bg-blue-50 flex flex-col items-center justify-center mb-4">
            <input 
              type="file" 
              accept=".csv" 
              onChange={handleFileChange}
              className="mb-2 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {file && <p className="text-sm text-gray-700">Fichier : <span className="font-bold">{file.name}</span></p>}
          </div>

          <button 
            onClick={handleUpload}
            disabled={loading || !file}
            className={`w-full py-3 rounded-xl font-bold text-white transition-all ${loading || !file ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-700 hover:bg-blue-800 shadow-md'}`}
          >
            {loading ? 'Analyse en cours...' : 'Importer et Calculer'}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 rounded">
              <p className="font-bold">Erreur</p>
              <p className="text-sm">{error}</p>
            </div>
          )}

          {result && (
            <div className="mt-6 border-t pt-6">
              <h3 className="font-bold text-gray-800 mb-2">📋 Résultat du calcul</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="bg-gray-50 p-3 rounded border"><span className="block text-xs text-gray-500">TVA Collectée</span><span className="font-bold text-blue-700">{result.bilan_fiscal.total_tva_collectee.toFixed(2)} MAD</span></div>
                <div className="bg-gray-50 p-3 rounded border"><span className="block text-xs text-gray-500">TVA Déductible</span><span className="font-bold text-green-700">{result.bilan_fiscal.total_tva_deductible.toFixed(2)} MAD</span></div>
                <div className="bg-gray-50 p-3 rounded border col-span-2 text-center"><span className="block text-xs text-gray-500">Net à payer</span><span className="text-xl font-bold text-red-700">{result.bilan_fiscal.tva_nette_a_payer.toFixed(2)} MAD</span></div>
              </div>
              <p className="text-center text-xs text-gray-500 mt-2">{result.message}</p>
            </div>
          )}
        </div>

        {/* --- PARTIE HISTORIQUE (TABLEAU DE BORD) --- */}
        <div className="bg-white shadow-xl rounded-2xl p-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-800">📅 Historique des déclarations</h2>
            <button onClick={fetchHistory} className="text-sm bg-gray-200 px-3 py-1 rounded hover:bg-gray-300">Actualiser</button>
          </div>

          {loadingHistory ? (
            <p className="text-center text-gray-500">Chargement de l'historique...</p>
          ) : history.length === 0 ? (
            <p className="text-center text-gray-500 py-8">Aucune déclaration enregistrée pour le moment. Importez votre premier fichier CSV !</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Mois</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Ventes HT</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">TVA Collectée</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Achats HT</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">TVA Déductible</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Net à Payer</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Échéance</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-500 uppercase">Statut</th>
                  </tr>
                </thead>
                
                {/* --- TABLEAU MIS À JOUR AVEC LE BOUTON PDF --- */}
                <tbody className="divide-y divide-gray-200">
                  {history.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">{item.mois}/{item.annee}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.total_ht_ventes.toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm text-blue-600 font-medium">{item.total_tva_collectee.toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.total_ht_achats.toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm text-green-600 font-medium">{item.total_tva_deductible.toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm font-bold text-red-600">{item.tva_nette_a_payer.toFixed(2)} MAD</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.echeance}</td>
                      <td className="py-3 px-4 text-sm">
                        <div className="flex flex-col gap-1">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            item.etat === 'Payée' ? 'bg-green-100 text-green-800' : 
                            item.etat.includes('En retard') ? 'bg-red-100 text-red-800' : 
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {item.etat}
                          </span>
                          
                          {/* BOUTON PDF (NOUVEAU) */}
                          <a 
                            href={`http://127.0.0.1:8000/declarations/${item.id}/pdf`} 
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-center bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-200 hover:bg-blue-100 transition"
                          >
                            📄 PDF
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
            </>
          )} />
        </Routes>

      </div>
    </div>
  )
}

export default App
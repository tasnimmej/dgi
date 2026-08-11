import { useState } from 'react'
import axios from 'axios'
import { getToken } from '../utils/auth'

export default function UploadInvoice() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [ocr, setOcr] = useState(null)
  const [message, setMessage] = useState(null)

  const handleFile = (e) => {
    setFile(e.target.files[0])
    setOcr(null)
    setMessage(null)
  }

  const handleUpload = async () => {
    if (!file) return alert('Sélectionnez une image ou un PDF')
    setLoading(true)
    setMessage(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await axios.post('http://127.0.0.1:8000/invoices/upload-invoice', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
        }
      })
      setOcr(res.data.ocr || res.data)
      setMessage(res.data.message)
    } catch (err) {
      console.error(err)
      setMessage(err.response?.data?.detail || 'Erreur OCR')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveManual = async () => {
    if (!ocr) return
    // map fields
    const payload = {
      date: ocr.date || null,
      ice_fournisseur: ocr.ice || '',
      montant_ht: ocr.montant_ht || 0,
      taux_tva: ocr.taux_tva || 0,
      type_transaction: 'VENTE'
    }

    try {
      const res = await axios.post('http://127.0.0.1:8000/invoices/manual-create', payload, {
        headers: {
          'Content-Type': 'application/json',
          ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
        }
      })
      setMessage(res.data.message + ' (ID: ' + res.data.invoice_id + ')')
      setOcr(null)
      setFile(null)
    } catch (err) {
      console.error(err)
      setMessage(err.response?.data?.detail || 'Erreur sauvegarde')
    }
  }

  return (
    <div className="min-h-screen p-6 bg-gray-50">
      <div className="max-w-2xl mx-auto bg-white p-6 rounded shadow">
        <h2 className="text-xl font-bold mb-4">Téléverser une facture (image / PDF)</h2>

        <input type="file" accept="image/*,.pdf" onChange={handleFile} className="mb-3" />
        <div className="flex gap-2">
          <button onClick={handleUpload} disabled={!file || loading} className="bg-blue-600 text-white px-4 py-2 rounded">{loading ? 'Analyse...' : 'Analyser (OCR)'}</button>
          {ocr && (
            <button onClick={handleSaveManual} className="bg-green-600 text-white px-4 py-2 rounded">Enregistrer (valider)</button>
          )}
        </div>

        {message && <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-400">{message}</div>}

        {ocr && (
          <div className="mt-4">
            <h3 className="font-bold mb-2">Résultats OCR (modifiable avant sauvegarde)</h3>
            <div className="grid grid-cols-1 gap-2">
              <div><strong>ICE :</strong> {ocr.ice}</div>
              <div><strong>Date :</strong> {ocr.date}</div>
              <div><strong>Montant HT :</strong> {ocr.montant_ht}</div>
              <div><strong>Taux TVA :</strong> {ocr.taux_tva}</div>
              <div className="mt-2"><strong>Texte brut extrait :</strong><pre className="text-xs whitespace-pre-wrap bg-gray-100 p-2 rounded">{ocr.raw_text}</pre></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

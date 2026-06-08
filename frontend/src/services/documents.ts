import apiClient from './api'

interface Document {
  id: string
  original_filename: string
  document_size_bytes: number
  upload_date: string
  processed: boolean
  metadata: Record<string, any>
}

interface UploadProgress {
  loaded: number
  total: number
  percent: number
}

export const documentService = {
  list: async (): Promise<Document[]> => {
    const response = await apiClient.get('/api/v1/documents')
    return response.data
  },

  upload: async (
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const total = progressEvent.total || 0
          const loaded = progressEvent.loaded
          onProgress({
            loaded,
            total,
            percent: total > 0 ? Math.round((loaded / total) * 100) : 0,
          })
        }
      },
    })

    return response.data
  },

  get: async (documentId: string): Promise<Document> => {
    const response = await apiClient.get(`/api/v1/documents/${documentId}`)
    return response.data
  },

  delete: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/documents/${documentId}`)
  },
}

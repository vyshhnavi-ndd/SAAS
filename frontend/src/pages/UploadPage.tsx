import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { documentService } from '../services/documents'
import styles from './UploadPage.module.css'

interface UploadProgress {
  loaded: number
  total: number
  percent: number
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<Record<string, UploadProgress>>({})
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      handleFiles(selectedFiles)
    }
  }

  const handleFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase()
      return ['pdf', 'txt', 'docx'].includes(ext || '')
    })

    if (validFiles.length !== newFiles.length) {
      setError(
        `Only PDF, TXT, and DOCX files are supported. ${newFiles.length - validFiles.length} file(s) were skipped.`
      )
    }

    setFiles([...files, ...validFiles])
    setError('')
  }

  const handleRemoveFile = (fileName: string) => {
    setFiles(files.filter((f) => f.name !== fileName))
  }

  const handleUploadAll = async () => {
    if (files.length === 0) return

    setUploading(true)
    setError('')
    setSuccess('')

    let uploadedCount = 0

    for (const file of files) {
      try {
        await documentService.upload(file, (prog) => {
          setProgress((prev) => ({
            ...prev,
            [file.name]: prog,
          }))
        })
        uploadedCount++
      } catch (err: any) {
        setError(
          (prev) =>
            (prev || '') +
            `\nFailed to upload ${file.name}: ${err.response?.data?.detail || err.message}`
        )
      }
    }

    setSuccess(`${uploadedCount} out of ${files.length} files uploaded successfully`)
    setFiles([])
    setProgress({})
    setUploading(false)

    // Redirect after success
    if (uploadedCount === files.length) {
      setTimeout(() => navigate('/dashboard'), 2000)
    }
  }

  const totalSize = files.reduce((sum, f) => sum + f.size, 0)
  const maxSize = 50 * 1024 * 1024
  const exceedsLimit = totalSize > maxSize

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button onClick={() => navigate('/dashboard')} className={styles.backBtn}>
          ← Back to Dashboard
        </button>
        <h1>Upload Documents</h1>
      </div>

      {error && <div className={styles.error}>{error}</div>}
      {success && <div className={styles.success}>{success}</div>}

      <div
        className={`${styles.dropZone} ${isDragging ? styles.dragging : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.dropContent}>
          <div className={styles.icon}>📁</div>
          <h2>Drop files here to upload</h2>
          <p>or click to browse</p>
          <p className={styles.supported}>Supported: PDF, DOCX, TXT (Max 50MB each)</p>
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleFileInput}
            className={styles.hiddenInput}
            id="fileInput"
          />
          <label htmlFor="fileInput" className={styles.browseBtn}>
            Choose Files
          </label>
        </div>
      </div>

      {files.length > 0 && (
        <div className={styles.filesList}>
          <h2>Files to Upload ({files.length})</h2>

          <div className={styles.sizeInfo}>
            <p>
              Total size: {(totalSize / 1024 / 1024).toFixed(2)} MB
              {exceedsLimit && <span className={styles.warning}> (Exceeds 50MB limit)</span>}
            </p>
          </div>

          <div className={styles.fileItems}>
            {files.map((file) => (
              <div key={file.name} className={styles.fileItem}>
                <div className={styles.fileInfo}>
                  <div className={styles.fileName}>{file.name}</div>
                  <div className={styles.fileSize}>
                    {(file.size / 1024).toFixed(2)} KB
                  </div>

                  {progress[file.name] && (
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${progress[file.name].percent}%` }}
                      />
                      <span className={styles.progressPercent}>
                        {progress[file.name].percent}%
                      </span>
                    </div>
                  )}
                </div>

                {!uploading && (
                  <button
                    onClick={() => handleRemoveFile(file.name)}
                    className={styles.removeBtn}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className={styles.actions}>
            <button
              onClick={() => setFiles([])}
              className={styles.clearBtn}
              disabled={uploading}
            >
              Clear All
            </button>
            <button
              onClick={handleUploadAll}
              className={styles.uploadBtn}
              disabled={uploading || exceedsLimit}
            >
              {uploading ? 'Uploading...' : 'Upload All'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

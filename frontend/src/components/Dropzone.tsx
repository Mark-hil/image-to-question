import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, CheckCircle, Image as ImageIcon, Sparkles } from 'lucide-react';

interface DropzoneProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
}

export const Dropzone: React.FC<DropzoneProps> = ({ selectedFile, onFileSelect }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File | null) => {
    if (!file) {
      onFileSelect(null);
      setPreviewUrl(null);
      return;
    }

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !selectedFile && fileInputRef.current?.click()}
      style={{
        border: `2px dashed ${isDragOver ? '#6366F1' : selectedFile ? '#10B981' : 'rgba(255, 255, 255, 0.14)'}`,
        background: isDragOver 
          ? 'rgba(99, 102, 241, 0.12)' 
          : selectedFile 
          ? 'rgba(16, 185, 129, 0.06)' 
          : 'rgba(15, 23, 42, 0.5)',
        borderRadius: '20px',
        padding: '36px 24px',
        textAlign: 'center',
        cursor: selectedFile ? 'default' : 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        boxShadow: isDragOver ? '0 0 30px rgba(99, 102, 241, 0.3)' : 'none'
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files && handleFile(e.target.files[0])}
        accept="image/*,.pdf"
        style={{ display: 'none' }}
      />

      {selectedFile ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          {previewUrl ? (
            <div style={{ position: 'relative' }}>
              <img
                src={previewUrl}
                alt="Worksheet Preview"
                style={{ 
                  maxHeight: '200px', 
                  maxWidth: '100%',
                  borderRadius: '14px', 
                  border: '1px solid rgba(255, 255, 255, 0.15)', 
                  objectFit: 'contain',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)'
                }}
              />
              <span className="badge badge-emerald" style={{ position: 'absolute', top: '10px', right: '10px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                <Sparkles size={12} /> Vision Ready
              </span>
            </div>
          ) : (
            <div style={{ padding: '24px', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '16px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
              <FileText size={56} color="#818CF8" />
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <span className="badge badge-emerald" style={{ padding: '6px 12px', fontSize: '0.82rem' }}>
              <CheckCircle size={14} /> Ready
            </span>
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#FFF' }}>{selectedFile.name}</span>
            <span style={{ color: '#64748B', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
              ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); handleFile(null); }}
              className="btn-danger"
              style={{ padding: '6px 12px', fontSize: '0.82rem', marginLeft: '6px' }}
              title="Remove File"
            >
              <X size={14} /> Remove
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
            padding: '18px',
            borderRadius: '50%',
            color: '#818CF8',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            boxShadow: '0 0 24px rgba(99, 102, 241, 0.2)'
          }} className="pulse-glow">
            <UploadCloud size={40} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '6px' }} className="text-gradient">
              Drag & Drop Worksheet Image or PDF
            </h3>
            <p style={{ fontSize: '0.88rem', color: '#94A3B8', maxWidth: '420px', margin: '0 auto 14px auto' }}>
              Upload textbook pages, diagrams, or PDF worksheets for automatic Vision AI question extraction.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <span className="badge badge-indigo"><ImageIcon size={12} /> PNG / JPG</span>
            <span className="badge badge-purple"><FileText size={12} /> PDF Document</span>
            <span className="badge badge-emerald"><Sparkles size={12} /> Groq Vision VLM</span>
          </div>
        </div>
      )}
    </div>
  );
};

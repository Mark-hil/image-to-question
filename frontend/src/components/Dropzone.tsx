import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, CheckCircle, Image as ImageIcon, Sparkles, Plus } from 'lucide-react';

interface DropzoneProps {
  selectedFiles?: File[];
  onFilesChange?: (files: File[]) => void;
  // Legacy single file props fallback
  selectedFile?: File | null;
  onFileSelect?: (file: File | null) => void;
}

export const Dropzone: React.FC<DropzoneProps> = ({
  selectedFiles,
  onFilesChange,
  selectedFile,
  onFileSelect
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Normalize files array from props
  const files: File[] = selectedFiles 
    ? selectedFiles 
    : selectedFile 
    ? [selectedFile] 
    : [];

  const updateFiles = (newFiles: File[]) => {
    if (onFilesChange) {
      onFilesChange(newFiles);
    }
    if (onFileSelect) {
      onFileSelect(newFiles.length > 0 ? newFiles[0] : null);
    }
  };

  const handleAddFiles = (incomingFileList: FileList | null) => {
    if (!incomingFileList || incomingFileList.length === 0) return;
    const incomingArr = Array.from(incomingFileList);
    // Combine with existing avoiding duplicate names
    const existingNames = new Set(files.map(f => `${f.name}_${f.size}`));
    const uniqueIncoming = incomingArr.filter(f => !existingNames.has(`${f.name}_${f.size}`));
    updateFiles([...files, ...uniqueIncoming]);
  };

  const handleRemoveFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    updateFiles(updated);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => {
        // If clicking empty dropzone background and no files attached
        if (files.length === 0) {
          fileInputRef.current?.click();
        }
      }}
      style={{
        border: `2px dashed ${isDragOver ? '#6366F1' : files.length > 0 ? '#10B981' : 'rgba(255, 255, 255, 0.14)'}`,
        background: isDragOver 
          ? 'rgba(99, 102, 241, 0.12)' 
          : files.length > 0 
          ? 'rgba(16, 185, 129, 0.04)' 
          : 'rgba(15, 23, 42, 0.5)',
        borderRadius: '20px',
        padding: files.length > 0 ? '24px 20px' : '36px 24px',
        textAlign: 'center',
        cursor: files.length > 0 ? 'default' : 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        boxShadow: isDragOver ? '0 0 30px rgba(99, 102, 241, 0.3)' : 'none'
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => {
          handleAddFiles(e.target.files);
          if (e.target) e.target.value = '';
        }}
        accept="image/*,.pdf,.pptx,.ppt"
        multiple
        style={{ display: 'none' }}
      />

      {files.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-emerald">
                <CheckCircle size={14} /> {files.length} Document{files.length > 1 ? 's' : ''} Attached
              </span>
              <span className="badge badge-indigo">
                <Sparkles size={12} /> Vision & OCR Ready
              </span>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: '0.82rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <Plus size={14} /> Add More Files
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  updateFiles([]);
                }}
                className="btn-danger"
                style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              >
                Clear All
              </button>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: '12px',
            maxHeight: '260px',
            overflowY: 'auto',
            paddingRight: '4px'
          }}>
            {files.map((file, idx) => {
              const isImage = file.type.startsWith('image/');
              return (
                <div
                  key={`${file.name}_${idx}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'rgba(30, 41, 59, 0.7)',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    gap: '10px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                    <div style={{
                      padding: '8px',
                      background: isImage ? 'rgba(99, 102, 241, 0.2)' : 'rgba(168, 85, 247, 0.2)',
                      borderRadius: '8px',
                      color: isImage ? '#818CF8' : '#C084FC',
                      display: 'flex'
                    }}>
                      {isImage ? <ImageIcon size={20} /> : <FileText size={20} />}
                    </div>
                    <div style={{ textAlign: 'left', overflow: 'hidden' }}>
                      <p style={{
                        fontSize: '0.88rem',
                        fontWeight: 600,
                        color: '#FFF',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        margin: 0
                      }}>
                        {file.name}
                      </p>
                      <span style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'var(--font-mono)' }}>
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFile(idx);
                    }}
                    style={{
                      background: 'rgba(239, 68, 68, 0.15)',
                      border: 'none',
                      color: '#EF4444',
                      borderRadius: '6px',
                      padding: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title="Remove file"
                  >
                    <X size={14} />
                  </button>
                </div>
              );
            })}
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
              Drag & Drop Worksheets, PDFs, or PowerPoint Slides
            </h3>
            <p style={{ fontSize: '0.88rem', color: '#94A3B8', maxWidth: '440px', margin: '0 auto 14px auto' }}>
              Upload textbook pages, image diagrams, PDF documents, or PPTX presentations for combined AI extraction.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <span className="badge badge-indigo"><ImageIcon size={12} /> PNG / JPG</span>
            <span className="badge badge-purple"><FileText size={12} /> PDF Worksheets</span>
            <span className="badge badge-indigo"><FileText size={12} /> PPTX Slides</span>
            <span className="badge badge-emerald"><Sparkles size={12} /> Multi-Doc AI</span>
          </div>
        </div>
      )}
    </div>
  );
};

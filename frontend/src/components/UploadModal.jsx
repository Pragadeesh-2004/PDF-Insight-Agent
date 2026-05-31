import React from "react";
import { Upload, X, Loader, CheckCircle, AlertCircle } from "lucide-react";

export function UploadModal({ isOpen, onClose, onUpload, isUploading }) {
  const [file, setFile] = React.useState(null);
  const [uploadStatus, setUploadStatus] = React.useState(null);
  const fileInputRef = React.useRef(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ];

      if (!validTypes.includes(selectedFile.type)) {
        setUploadStatus({
          type: "error",
          message: "Only PDF and Word documents are supported",
        });
        return;
      }

      if (selectedFile.size > 10 * 1024 * 1024) {
        setUploadStatus({
          type: "error",
          message: "File size must be less than 10MB",
        });
        return;
      }

      setFile(selectedFile);
      setUploadStatus(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (file) {
      try {
        await onUpload(file);
        setUploadStatus({
          type: "success",
          message: "Document uploaded successfully!",
        });
        setFile(null);
        setTimeout(() => {
          onClose();
          setUploadStatus(null);
        }, 1500);
      } catch (error) {
        setUploadStatus({
          type: "error",
          message: error.message || "Upload failed",
        });
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="glass rounded-xl p-6 w-full max-w-md border border-white/20">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold gradient-text">Upload Document</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-all"
            disabled={isUploading}
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File Input */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-white/5 transition-all"
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              accept=".pdf,.docx"
              disabled={isUploading}
              className="hidden"
            />
            <Upload size={32} className="mx-auto mb-2 text-white/60" />
            <p className="font-semibold mb-1">
              {file ? file.name : "Click to upload or drag file"}
            </p>
            <p className="text-sm text-white/50">
              PDF or Word documents (max 10MB)
            </p>
          </div>

          {/* Status Messages */}
          {uploadStatus && (
            <div
              className={`flex items-center gap-2 p-3 rounded-lg ${
                uploadStatus.type === "error"
                  ? "bg-red-500/20 text-red-200"
                  : "bg-green-500/20 text-green-200"
              }`}
            >
              {uploadStatus.type === "error" ? (
                <AlertCircle size={20} />
              ) : (
                <CheckCircle size={20} />
              )}
              <p className="text-sm">{uploadStatus.message}</p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading}
              className="flex-1 px-4 py-2 rounded-lg glass hover:bg-white/10 font-semibold transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || isUploading}
              className="flex-1 px-4 py-2 rounded-lg bg-gradient-primary hover:shadow-lg hover:shadow-blue-500/50 font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader size={18} className="animate-spin" />
                  Uploading...
                </>
              ) : (
                "Upload"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UploadModal;

"use client";

import { useState } from "react";
import { Check, X, Send, Image as ImageIcon } from "lucide-react";

interface ApprovalQueueProps {
  campaignId: string;
  queue: any[];
  onApprove: (entryIndex: number) => Promise<void>;
  onReject: (entryIndex: number) => Promise<void>;
  onPublish: (entryIndices: number[]) => Promise<void>;
  onCaptionEdit?: (entryIndex: number, newCaption: string) => void;
}

export default function ApprovalQueue({
  campaignId,
  queue,
  onApprove,
  onReject,
  onPublish,
  onCaptionEdit,
}: ApprovalQueueProps) {
  const [selectedEntries, setSelectedEntries] = useState<Set<number>>(new Set());
  const [processingEntry, setProcessingEntry] = useState<number | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [editedCaptions, setEditedCaptions] = useState<Record<number, string>>({});
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

  const toggleSelection = (index: number) => {
    const newSelected = new Set(selectedEntries);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedEntries(newSelected);
  };

  const handleApprove = async (index: number) => {
    setProcessingEntry(index);
    try {
      await onApprove(index);
      // Auto-select approved entries
      setSelectedEntries((prev) => new Set([...prev, index]));
    } finally {
      setProcessingEntry(null);
    }
  };

  const handleReject = async (index: number) => {
    setProcessingEntry(index);
    try {
      await onReject(index);
      // Remove from selection if rejected
      setSelectedEntries((prev) => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    } finally {
      setProcessingEntry(null);
    }
  };

  const handlePublishSelected = async () => {
    if (selectedEntries.size === 0) return;
    setPublishing(true);
    try {
      await onPublish(Array.from(selectedEntries));
    } finally {
      setPublishing(false);
    }
  };

  const approvedCount = queue.filter((e) => e.approval_status === "approved").length;
  const pendingCount = queue.filter((e) => e.approval_status === "pending").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Approval Queue</h2>
        <p className="text-gray-600">
          Review and approve content before publishing to social media
        </p>
        <div className="flex gap-4 mt-4">
          <div className="px-4 py-2 bg-yellow-50 rounded-lg">
            <span className="text-yellow-700 font-semibold">{pendingCount} Pending</span>
          </div>
          <div className="px-4 py-2 bg-green-50 rounded-lg">
            <span className="text-green-700 font-semibold">{approvedCount} Approved</span>
          </div>
        </div>
      </div>

      {/* Queue Items */}
      <div className="space-y-4">
        {queue.map((entry, idx) => (
          <div
            key={idx}
            className={`bg-white rounded-xl shadow-lg border-2 transition-all ${
              entry.approval_status === "approved"
                ? "border-green-300 bg-green-50/30"
                : entry.approval_status === "rejected"
                ? "border-red-300 bg-red-50/30"
                : selectedEntries.has(idx)
                ? "border-indigo-400"
                : "border-gray-200"
            }`}
          >
            <div className="p-6">
              <div className="flex items-start gap-6">
                {/* Image Preview - Always visible, clickable to enlarge */}
                <div className="flex-shrink-0 relative group">
                  {entry.image_info?.generated_url ? (
                    <>
                      <img
                        src={`http://localhost:8000${entry.image_info.generated_url}`}
                        alt={`Generated content ${idx + 1}`}
                        className="w-48 h-48 object-cover rounded-lg shadow-md cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => setEnlargedImage(`http://localhost:8000${entry.image_info.generated_url}`)}
                        onError={(e) => {
                          console.error("Image failed to load:", entry.image_info.generated_url);
                          e.currentTarget.style.display = 'none';
                          const placeholder = e.currentTarget.parentElement?.querySelector('.placeholder');
                          if (placeholder) {
                            placeholder.classList.remove('hidden');
                          }
                        }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-30 rounded-lg transition-all pointer-events-none">
                        <span className="text-white text-sm font-semibold opacity-0 group-hover:opacity-100">
                          🔍 Click to enlarge
                        </span>
                      </div>
                    </>
                  ) : null}
                  <div className={`placeholder w-48 h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center ${entry.image_info?.generated_url ? 'hidden' : ''}`}>
                    <ImageIcon className="w-12 h-12 text-gray-400 mb-2" />
                    <p className="text-xs text-gray-500 text-center px-2">No image available</p>
                  </div>
                </div>

                {/* Content Details - Always visible */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                        {entry.channel}
                      </span>
                      <span className="text-sm text-gray-500">
                        {entry.date} at {entry.time}
                      </span>
                    </div>
                    {entry.approval_status === "approved" && (
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        ✓ Approved
                      </span>
                    )}
                    {entry.approval_status === "rejected" && (
                      <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                        ✗ Rejected
                      </span>
                    )}
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Caption: {entry.approval_status === "pending" && <span className="text-xs text-gray-500">(editable)</span>}
                    </label>
                    <textarea
                      value={editedCaptions[idx] !== undefined ? editedCaptions[idx] : (entry.caption || "No caption available")}
                      onChange={(e) => {
                        setEditedCaptions({ ...editedCaptions, [idx]: e.target.value });
                        if (onCaptionEdit) {
                          onCaptionEdit(idx, e.target.value);
                        }
                      }}
                      className="w-full bg-white border border-gray-300 rounded-lg p-3 text-gray-800 min-h-[100px] focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600"
                      disabled={entry.approval_status !== "pending"}
                    />
                  </div>

                  {entry.image_info && (
                    <div className="text-sm text-gray-600 space-y-1 mb-4">
                      <p>
                        <strong>Layout:</strong> {entry.image_info.layout}
                      </p>
                      <p>
                        <strong>Text Overlay:</strong> {entry.image_info.text_overlay}
                      </p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {entry.approval_status === "pending" && (
                    <div className="flex gap-3 mt-4">
                      <button
                        onClick={() => handleApprove(idx)}
                        disabled={processingEntry === idx}
                        className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                      >
                        <Check className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(idx)}
                        disabled={processingEntry === idx}
                        className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                      >
                        <X className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Publish Button */}
      {approvedCount > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Ready to Publish</h3>
              <p className="text-gray-600 text-sm">
                {approvedCount} approved post{approvedCount !== 1 ? "s" : ""} ready for Instagram & Facebook
              </p>
            </div>
            <button
              onClick={handlePublishSelected}
              disabled={publishing || approvedCount === 0}
              className="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 transition-all shadow-lg font-semibold"
            >
              <Send className="w-5 h-5" />
              {publishing ? "Publishing..." : `Publish ${approvedCount} Post${approvedCount !== 1 ? "s" : ""}`}
            </button>
          </div>
        </div>
      )}

      {/* Image Enlargement Modal */}
      {enlargedImage && (
        <div 
          className="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center p-4"
          onClick={() => setEnlargedImage(null)}
        >
          <div className="relative max-w-6xl max-h-[90vh]">
            <button
              onClick={() => setEnlargedImage(null)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 text-lg font-bold px-4 py-2"
            >
              ✕ Close
            </button>
            <img
              src={enlargedImage}
              alt="Enlarged preview"
              className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
}

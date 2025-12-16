"use client";

import { useState } from "react";
import { Send, Paperclip, Loader2, Sparkles, Calendar, Image, Video, FileText, TrendingUp, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import dynamic from "next/dynamic";

const ApprovalQueue = dynamic(() => import("@/components/ApprovalQueue"), { ssr: false });

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [showApprovalQueue, setShowApprovalQueue] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setResult(null);

    try {
      // First check if backend is healthy
      const healthCheck = await fetch("/api/health", {
        method: "GET",
        signal: AbortSignal.timeout(5000), // 5 second timeout for health check
      });
      
      if (!healthCheck.ok) {
        throw new Error("Backend is not responding. Please check if the server is running.");
      }

      // Create abort controller with 10 minute timeout for long-running operations
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes

      // Start campaign in background mode
      const response = await fetch("/api/campaign/start?background=true", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          goal: input,
          channels: ["Instagram", "Facebook"],
          timeframe: "1 week",
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.detail?.error || "Failed to start campaign");
        (error as any).response = response;
        throw error;
      }

      const startData = await response.json();
      console.log("Campaign started:", startData);

      if (startData.campaign_id) {
        // Show progress message
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `⏳ Campaign started (ID: ${startData.campaign_id}). Generating content... This may take 5-10 minutes.`,
          },
        ]);

        // Poll for status
        const campaignId = startData.campaign_id;
        setCampaignId(campaignId); // Store campaign ID for approval
        const pollInterval = 3000; // 3 seconds
        const maxPolls = 300; // 15 minutes max
        let pollCount = 0;

        const pollStatus = async () => {
          try {
            const statusResponse = await fetch(`/api/campaign/${campaignId}/status`);
            if (!statusResponse.ok) throw new Error("Failed to fetch status");

            const statusData = await statusResponse.json();
            console.log("Status:", statusData);

            if (statusData.status === "completed") {
              // Fetch full campaign data
              const dataResponse = await fetch(`/api/campaign/${campaignId}/data`);
              const data = await dataResponse.json();
              console.log("Received data:", data);
              return data;
            } else if (statusData.status === "failed") {
              throw new Error(statusData.error || "Campaign generation failed");
            } else if (statusData.status === "running") {
              // Update progress
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === "assistant" && lastMsg.content.startsWith("⏳")) {
                  lastMsg.content = `⏳ ${statusData.progress || "Generating content..."}`;
                }
                return newMessages;
              });

              // Continue polling
              pollCount++;
              if (pollCount < maxPolls) {
                await new Promise((resolve) => setTimeout(resolve, pollInterval));
                return await pollStatus();
              } else {
                throw new Error("Campaign generation timed out after 15 minutes");
              }
            }
          } catch (error) {
            console.error("Polling error:", error);
            throw error;
          }
        };

        const data = await pollStatus();
        console.log("Final data:", data);

        if (data.data || data.strategy) {
          const resultData = data.data || data;
          setResult(resultData);
          
          // Check if awaiting approval
          if (resultData.publish_result?.status === "awaiting_approval") {
            setShowApprovalQueue(true);
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: "✨ Campaign generated! Images created successfully. Please review and approve content before publishing to Instagram & Facebook.",
              },
            ]);
          } else {
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: "✨ Campaign generated successfully! Check out the results below.",
              },
            ]);
          }
        } else {
          console.error("No data in response:", data);
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: "⚠️ Campaign generated but no data received. Check console." },
          ]);
        }
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "❌ Failed to start campaign. No campaign ID received." },
        ]);
      }
    } catch (error: any) {
      console.error("Error:", error);
      let errorMessage = "❌ Error: Failed to generate campaign. Please check backend logs.";
      
      if (error.name === 'AbortError') {
        errorMessage = "⏱️ Request timed out. The AI agents are still working - please wait and try refreshing.";
      } else if (error.message?.includes('socket hang up') || error.message?.includes('ECONNRESET')) {
        errorMessage = "🔌 Connection lost. The backend may have crashed or timed out. Please check backend logs and try again.";
      } else if (error.response?.status === 504) {
        errorMessage = "⏱️ Campaign generation timed out (15 minutes). Try with a simpler request.";
      } else if (error.response?.status === 500) {
        errorMessage = `❌ Backend error: ${error.message || 'Check backend terminal for details.'}`;
      }
      
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: errorMessage },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Approval handlers
  const handleApprove = async (entryIndex: number) => {
    if (!campaignId) return;
    try {
      const response = await fetch(`/api/approval/${campaignId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_index: entryIndex, action: "approve" }),
      });
      if (!response.ok) throw new Error("Failed to approve");
      
      // Reload approval queue
      const queueResponse = await fetch(`/api/approval/${campaignId}/queue`);
      const queueData = await queueResponse.json();
      if (result) {
        result.calendar = { entries: queueData.queue };
        setResult({ ...result });
      }
    } catch (error) {
      console.error("Approval error:", error);
      alert("Failed to approve entry");
    }
  };

  const handleReject = async (entryIndex: number) => {
    if (!campaignId) return;
    try {
      const response = await fetch(`/api/approval/${campaignId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_index: entryIndex, action: "reject" }),
      });
      if (!response.ok) throw new Error("Failed to reject");
      
      // Reload approval queue
      const queueResponse = await fetch(`/api/approval/${campaignId}/queue`);
      const queueData = await queueResponse.json();
      if (result) {
        result.calendar = { entries: queueData.queue };
        setResult({ ...result });
      }
    } catch (error) {
      console.error("Reject error:", error);
      alert("Failed to reject entry");
    }
  };

  const handlePublish = async (entryIndices: number[]) => {
    if (!campaignId) return;
    try {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "📤 Publishing to Instagram & Facebook..." },
      ]);

      const response = await fetch(`/api/approval/${campaignId}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          entry_indices: entryIndices,
          platforms: ["instagram", "facebook"]
        }),
      });
      
      if (!response.ok) throw new Error("Failed to publish");
      
      const publishResult = await response.json();
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: `✅ Successfully published ${publishResult.published_count} posts! ${publishResult.failed_count > 0 ? `(${publishResult.failed_count} failed)` : ""}` 
        },
      ]);
      
      setShowApprovalQueue(false);
    } catch (error) {
      console.error("Publish error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Failed to publish. Check console for details." },
      ]);
    }
  };

  const handleCaptionEdit = (entryIndex: number, newCaption: string) => {
    if (result && result.calendar?.entries) {
      result.calendar.entries[entryIndex].caption = newCaption;
      setResult({ ...result });
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                AI Content Generator
              </h1>
              <p className="text-xs text-gray-500">Powered by MAF DAG</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              {/* Chat Messages */}
              <div className="h-[500px] overflow-y-auto p-6 space-y-4">
                {messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center mb-4">
                      <Sparkles className="w-10 h-10 text-indigo-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">
                      Create Your Campaign
                    </h2>
                    <p className="text-gray-500 max-w-md mb-6">
                      Describe your social media campaign goal, and our AI agents will create a complete strategy with content.
                    </p>
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 max-w-md">
                      <p className="text-sm font-medium text-gray-700 mb-2">💡 Try this:</p>
                      <p className="text-sm text-gray-600 italic">
                        "Promote AI Conclave 2025 on Instagram and Facebook for 7 days to attract students"
                      </p>
                    </div>
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-2xl ${msg.role === "user"
                        ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                        : "bg-gradient-to-r from-gray-50 to-gray-100 text-gray-800 shadow-sm border border-gray-200"
                        }`}
                    >
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 p-4 rounded-2xl shadow-sm">
                      <div className="flex items-center gap-3 mb-2">
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                        <span className="text-sm text-gray-600 font-medium">AI agents are working...</span>
                      </div>
                      <p className="text-xs text-gray-500 ml-8">This may take 30-60 seconds as we run 6 AI agents</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="p-4 bg-gray-50 border-t border-gray-200">
                <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
                  <button
                    type="button"
                    className="p-3 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                    title="Attach file"
                  >
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe your campaign goal..."
                    className="flex-1 p-4 pr-14 rounded-xl border-2 border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white shadow-sm transition-all text-gray-900 placeholder-gray-400"
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="absolute right-2 p-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </div>
          </div>

          {/* Stats/Info Section */}
          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                Quick Stats
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl">
                  <span className="text-sm font-medium text-gray-700">Campaigns</span>
                  <span className="text-lg font-bold text-indigo-600">{messages.filter(m => m.role === "user").length}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl">
                  <span className="text-sm font-medium text-gray-700">Generated</span>
                  <span className="text-lg font-bold text-green-600">{result ? 1 : 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4">AI Agents</h3>
              <div className="space-y-2 text-sm">
                {["Strategy", "Research", "Brand Voice", "Content", "Calendar", "Publisher"].map((agent, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">{agent}Agent</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        {/* Approval Queue */}
        {showApprovalQueue && result && campaignId && (
          <div className="mt-8">
            <ApprovalQueue
              campaignId={campaignId}
              queue={result.calendar?.entries || []}
              onApprove={handleApprove}
              onReject={handleReject}
              onPublish={handlePublish}
              onCaptionEdit={handleCaptionEdit}
            />
          </div>
        )}

        {result && !showApprovalQueue && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <ResultCard
              icon={<FileText className="w-6 h-6" />}
              title="Strategy"
              color="indigo"
              data={result.strategy}
              onClick={() => setSelectedCard("strategy")}
            />
            <ResultCard
              icon={<Calendar className="w-6 h-6" />}
              title="Calendar"
              color="purple"
              data={result.calendar}
              onClick={() => setSelectedCard("calendar")}
            />
            <ResultCard
              icon={<Image className="w-6 h-6" />}
              title="Images"
              color="pink"
              data={result.content?.image_briefs}
              onClick={() => setSelectedCard("images")}
            />
            <ResultCard
              icon={<Video className="w-6 h-6" />}
              title="Videos"
              color="blue"
              data={result.content?.video_scripts}
              onClick={() => setSelectedCard("videos")}
            />
          </div>
        )}

        {/* Modal for detailed view */}
        {selectedCard && (
          <DetailModal
            title={selectedCard}
            data={
              selectedCard === "strategy" ? result.strategy :
                selectedCard === "calendar" ? result.calendar :
                  selectedCard === "images" ? result.content?.image_briefs :
                    result.content?.video_scripts
            }
            onClose={() => setSelectedCard(null)}
          />
        )}
      </div>
    </main>
  );
}

function ResultCard({ icon, title, color, data, onClick }: any) {
  const colors = {
    indigo: "from-indigo-500 to-indigo-600",
    purple: "from-purple-500 to-purple-600",
    pink: "from-pink-500 to-pink-600",
    blue: "from-blue-500 to-blue-600",
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 hover:shadow-2xl transition-all cursor-pointer hover:scale-105"
    >
      <div className={`w-12 h-12 bg-gradient-to-br ${colors[color as keyof typeof colors]} rounded-xl flex items-center justify-center text-white mb-4`}>
        {icon}
      </div>
      <h3 className="text-lg font-bold text-gray-800 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">
        {Array.isArray(data) ? `${data.length} items` : "Available"}
      </p>
    </div>
  );
}

function DetailModal({ title, data, onClose }: any) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <h2 className="text-2xl font-bold capitalize bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white rounded-xl transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-100px)]">
          {title === "strategy" && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Content Pillars</h3>
                <ul className="list-disc list-inside space-y-1">
                  {data.pillars?.map((p: string, i: number) => (
                    <li key={i} className="text-gray-700">{p}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Post Types by Channel</h3>
                {Object.entries(data.post_types_by_channel || {}).map(([channel, types]: [string, any]) => (
                  <div key={channel} className="mb-2">
                    <p className="font-medium text-indigo-600">{channel}:</p>
                    <p className="text-gray-700 ml-4">{types.join(", ")}</p>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Frequency Plan</h3>
                <p className="text-gray-700">{data.frequency_plan}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">Success Metrics</h3>
                <ul className="list-disc list-inside space-y-1">
                  {data.success_metrics?.map((m: string, i: number) => (
                    <li key={i} className="text-gray-700">{m}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          {title === "calendar" && (
            <div className="space-y-4">
              {data.entries?.map((entry: any, i: number) => (
                <div key={i} className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-800">{entry.date} at {entry.time}</span>
                    <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">{entry.channel}</span>
                  </div>
                  <p className="text-gray-700"><strong>Type:</strong> {entry.post_type}</p>
                  <p className="text-gray-600 text-sm mt-1">Caption: {entry.caption_ref}</p>
                </div>
              ))}</div>
          )}
          {title === "images" && (
            <div className="space-y-4">
              {data?.map((brief: any, i: number) => (
                <div key={i} className="p-4 bg-gradient-to-r from-pink-50 to-rose-50 rounded-xl border border-pink-200">
                  <h4 className="font-semibold text-gray-800 mb-2">Image Brief #{i + 1}</h4>
                  <p className="text-gray-700 mb-2"><strong>Layout:</strong> {brief.layout_description}</p>
                  <p className="text-gray-700 mb-2"><strong>Text Overlay:</strong> {brief.text_overlay}</p>
                  <p className="text-gray-700"><strong>Style:</strong> {brief.style_suggestions}</p>
                </div>
              ))}
            </div>
          )}
          {title === "videos" && (
            <div className="space-y-4">
              {data?.map((script: any, i: number) => (
                <div key={i} className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
                  <h4 className="font-semibold text-gray-800 mb-2">Video Script #{i + 1}</h4>
                  <p className="text-gray-700 mb-2"><strong>Script:</strong> {script.script_content}</p>
                  <p className="text-gray-700 mb-2"><strong>Scenes:</strong> {script.scene_instructions}</p>
                  <p className="text-gray-700"><strong>Voice Over:</strong> {script.voice_over}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

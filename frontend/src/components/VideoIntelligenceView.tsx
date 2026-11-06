import React, { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Film,
  Layers,
  Pause,
  Play,
  Search,
  Sparkles,
  Volume2,
  VolumeX,
} from "lucide-react";
import { api } from "@/services/api";
import { VideoDocument } from "@/types/api";

interface VideoIntelligenceViewProps {
  fileId: string;
  filename: string;
  format?: string;
}

export const VideoIntelligenceView: React.FC<VideoIntelligenceViewProps> = ({
  fileId,
  filename,
  format,
}) => {
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement>(null);

  const [activeTab, setActiveTab] = useState<
    "overview" | "scenes" | "timeline" | "transcript" | "tracks"
  >("overview");
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [searchQuery, setSearchQuery] = useState("");

  // Queries
  const {
    data: documentData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["video-document", fileId],
    queryFn: () => api.getVideoDocumentResult(fileId),
    retry: 1,
  });

  // Mutation to trigger video analysis
  const analyzeMutation = useMutation({
    mutationFn: (options?: Record<string, unknown>) =>
      api.analyzeVideoFile(fileId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["video-document", fileId] });
      queryClient.invalidateQueries({ queryKey: ["video-analysis", fileId] });
    },
  });

  // Video playback handlers
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (timeSeconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeSeconds;
      setCurrentTime(timeSeconds);
    }
  };

  const handlePlaybackRateChange = (rate: number) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const formatSeconds = (sec: number) => {
    const s = Math.floor(sec);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const remainder = s % 60;
    if (hrs > 0) {
      return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${remainder.toString().padStart(2, "0")}`;
    }
    return `${mins.toString().padStart(2, "0")}:${remainder.toString().padStart(2, "0")}`;
  };

  const doc: VideoDocument | undefined = documentData;
  const vStream = doc?.video_streams?.[0];
  const aStream = doc?.audio_streams?.[0];

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-lg">
              <Film className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-foreground">{filename}</h2>
                <span className="text-xs px-2 py-0.5 font-semibold bg-muted text-muted-foreground rounded uppercase">
                  {doc?.format || format || "video"}
                </span>
                {doc ? (
                  <span className="text-xs px-2 py-0.5 font-medium bg-emerald-500/10 text-emerald-600 rounded flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {doc.processing_status}
                  </span>
                ) : (
                  <span className="text-xs px-2 py-0.5 font-medium bg-amber-500/10 text-amber-600 rounded">
                    Analysis Pending
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {doc ? (
                  <>
                    Resolution: {vStream?.resolution || "N/A"} • {vStream ? `${vStream.fps.toFixed(1)} fps` : ""}{" "}
                    • Duration: {formatSeconds(doc.duration)} • Scenes: {doc.scenes.length} • Tracks: {doc.tracks.length}
                  </>
                ) : (
                  "Video & Visual Intelligence analysis pending"
                )}
              </p>
            </div>
          </div>

          {/* Action / Export Controls */}
          {doc ? (
            <div className="flex items-center gap-2 flex-wrap">
              <a
                href={api.getVideoExportUrl(fileId, "json")}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-muted text-foreground rounded-lg hover:bg-muted/80 transition"
              >
                <Download className="w-3.5 h-3.5" />
                JSON
              </a>
              <a
                href={api.getVideoExportUrl(fileId, "markdown")}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-muted text-foreground rounded-lg hover:bg-muted/80 transition"
              >
                <FileText className="w-3.5 h-3.5" />
                Markdown
              </a>
              <a
                href={api.getVideoExportUrl(fileId, "srt")}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-muted text-foreground rounded-lg hover:bg-muted/80 transition"
              >
                <Download className="w-3.5 h-3.5" />
                SRT
              </a>
              <a
                href={api.getVideoExportUrl(fileId, "vtt")}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-muted text-foreground rounded-lg hover:bg-muted/80 transition"
              >
                <Download className="w-3.5 h-3.5" />
                VTT
              </a>
            </div>
          ) : (
            <button
              onClick={() => analyzeMutation.mutate({})}
              disabled={analyzeMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 transition shadow-sm disabled:opacity-50"
            >
              {analyzeMutation.isPending ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  <span>Analyzing Video...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Analyze Video Intelligence</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center p-12 bg-card rounded-xl border border-border">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-3" />
          <h3 className="text-sm font-semibold text-foreground">Processing Video Intelligence...</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Decoding streams, detecting scene boundaries, and synchronizing audio transcript.
          </p>
        </div>
      )}

      {(isError || !doc) && !isLoading && (
        <div className="bg-card rounded-xl border border-border p-8 text-center">
          <Film className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-60" />
          <h3 className="text-lg font-semibold text-foreground">No Video Intelligence Analysis Available</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mt-1 mb-6">
            This video has not yet been processed for scene cuts, OCR, object tracking, or audio synchronization.
          </p>
          <button
            onClick={() => analyzeMutation.mutate({})}
            disabled={analyzeMutation.isPending}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition shadow-sm disabled:opacity-50"
          >
            {analyzeMutation.isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                <span>Analyzing Video...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Analyze Video Intelligence</span>
              </>
            )}
          </button>
          {analyzeMutation.isError && (
            <div className="mt-4 p-3 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center justify-center gap-2 max-w-md mx-auto">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>Analysis failed: {(analyzeMutation.error as Error).message}</span>
            </div>
          )}
        </div>
      )}

      {doc && (
        <>
          {/* Main Interactive Video Player */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            <div className="relative rounded-lg overflow-hidden bg-black aspect-video flex items-center justify-center">
              <video
                ref={videoRef}
                src={`/api/v1/files/${encodeURIComponent(fileId)}/content`}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onEnded={() => setIsPlaying(false)}
                className="w-full h-full object-contain"
              />
            </div>

            {/* Video Scrubber & Playback Controls */}
            <div className="space-y-2">
              <input
                type="range"
                min={0}
                max={duration || doc.duration || 100}
                step={0.1}
                value={currentTime}
                onChange={(e) => handleSeek(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
              />

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-3">
                  <button
                    onClick={togglePlay}
                    className="p-2 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition shadow-sm"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>

                  <button
                    onClick={toggleMute}
                    className="p-1.5 text-foreground hover:bg-muted rounded-md transition"
                  >
                    {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </button>

                  <span className="font-mono text-foreground font-medium">
                    {formatSeconds(currentTime)} / {formatSeconds(duration || doc.duration)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground font-medium">Speed:</span>
                  {[0.5, 1.0, 1.25, 1.5, 2.0].map((rate) => (
                    <button
                      key={rate}
                      onClick={() => handlePlaybackRateChange(rate)}
                      className={`px-2 py-0.5 rounded text-xs font-medium transition ${
                        playbackRate === rate
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-border flex items-center gap-2">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                activeTab === "overview"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Activity className="w-4 h-4" />
              Overview & Metrics
            </button>
            <button
              onClick={() => setActiveTab("scenes")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                activeTab === "scenes"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Film className="w-4 h-4" />
              Scenes ({doc.scenes.length})
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                activeTab === "timeline"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Clock className="w-4 h-4" />
              Multimodal Timeline ({doc.timeline.length})
            </button>
            <button
              onClick={() => setActiveTab("transcript")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                activeTab === "transcript"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-4 h-4" />
              Speech Transcript
            </button>
            <button
              onClick={() => setActiveTab("tracks")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                activeTab === "tracks"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="w-4 h-4" />
              Tracked Objects ({doc.tracks.length})
            </button>
          </div>

          {/* Tab 1: Overview */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Video Stream</span>
                <div className="text-xl font-bold text-foreground mt-1">{vStream?.resolution || "0x0"}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Codec: {vStream?.codec || "Unknown"} • {vStream ? `${vStream.fps.toFixed(1)} FPS` : ""}
                </p>
              </div>

              <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Audio Stream</span>
                <div className="text-xl font-bold text-foreground mt-1">
                  {aStream ? `${aStream.codec.toUpperCase()} (${aStream.sample_rate}Hz)` : "None"}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Layout: {aStream?.channel_layout || "No audio track"}
                </p>
              </div>

              <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Visual Intelligence</span>
                <div className="text-xl font-bold text-foreground mt-1">{doc.scenes.length} Scenes</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {doc.keyframes.length} keyframes • {doc.tracks.length} tracked entities
                </p>
              </div>

              <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Speech & Audio</span>
                <div className="text-xl font-bold text-foreground mt-1">
                  {doc.transcript ? `${doc.transcript.split(/\s+/).length} Words` : "No Speech"}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {doc.speakers.length} speakers • {doc.transcript_segments.length} utterances
                </p>
              </div>
            </div>
          )}

          {/* Tab 2: Scenes Navigator */}
          {activeTab === "scenes" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {doc.scenes.map((sc, idx) => (
                <div
                  key={sc.scene_id}
                  className={`bg-card border rounded-xl p-4 transition shadow-sm cursor-pointer ${
                    currentTime >= sc.start && currentTime <= sc.end
                      ? "border-primary ring-1 ring-primary"
                      : "border-border hover:border-foreground/40"
                  }`}
                  onClick={() => handleSeek(sc.start)}
                >
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                    <span className="font-semibold text-foreground font-mono">
                      Scene #{idx + 1} ({sc.scene_id})
                    </span>
                    <span className="px-2 py-0.5 rounded bg-muted text-foreground font-mono">
                      {formatSeconds(sc.start)} – {formatSeconds(sc.end)}
                    </span>
                  </div>

                  <p className="text-sm text-foreground/90 font-medium mb-3">
                    {sc.visual_summary || `Visual scene transition (${sc.transition_type})`}
                  </p>

                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
                    <span>Duration: {sc.duration.toFixed(2)}s</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSeek(sc.start);
                      }}
                      className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                    >
                      <Play className="w-3 h-3" />
                      Jump to scene
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Multimodal Timeline */}
          {activeTab === "timeline" && (
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-3">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Chronological Multimodal Signals
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                {doc.timeline.map((item) => (
                  <div
                    key={item.event_id}
                    onClick={() => handleSeek(item.start)}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/40 transition cursor-pointer text-sm"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs text-muted-foreground px-2 py-1 bg-muted rounded">
                        {formatSeconds(item.start)} – {formatSeconds(item.end)}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 font-semibold rounded uppercase ${
                          item.event_type === "scene"
                            ? "bg-blue-500/10 text-blue-600"
                            : item.event_type === "speech"
                            ? "bg-emerald-500/10 text-emerald-600"
                            : item.event_type === "ocr"
                            ? "bg-amber-500/10 text-amber-600"
                            : "bg-purple-500/10 text-purple-600"
                        }`}
                      >
                        {item.event_type}
                      </span>
                      <span className="font-medium text-foreground">{item.summary}</span>
                    </div>
                    <Play className="w-3.5 h-3.5 text-muted-foreground opacity-60 hover:opacity-100" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 4: Synchronized Speech Transcript */}
          {activeTab === "transcript" && (
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search transcript..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-sm bg-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <span className="text-xs text-muted-foreground">
                  {doc.transcript_segments.length} segments • {doc.speakers.length} speakers
                </span>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {doc.transcript_segments
                  .filter((seg) =>
                    searchQuery ? seg.text.toLowerCase().includes(searchQuery.toLowerCase()) : true
                  )
                  .map((seg) => (
                    <div
                      key={seg.segment_id}
                      onClick={() => handleSeek(seg.start)}
                      className={`p-3 rounded-lg border transition cursor-pointer ${
                        currentTime >= seg.start && currentTime <= seg.end
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/40"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                        <span className="font-semibold text-primary">{seg.speaker_id || "Speaker"}</span>
                        <span className="font-mono">
                          {formatSeconds(seg.start)} – {formatSeconds(seg.end)}
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{seg.text}</p>
                    </div>
                  ))}
                {doc.transcript_segments.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No speech transcript found in this video recording.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Tab 5: Tracked Objects */}
          {activeTab === "tracks" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {doc.tracks.map((tr) => (
                <div
                  key={tr.track_id}
                  onClick={() => handleSeek(tr.first_seen_seconds)}
                  className="bg-card border border-border rounded-xl p-4 shadow-sm hover:border-primary transition cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 bg-muted text-foreground rounded">
                      {tr.track_id}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 bg-purple-500/10 text-purple-600 rounded capitalize">
                      {tr.object_class}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Visible: {formatSeconds(tr.first_seen_seconds)} to {formatSeconds(tr.last_seen_seconds)} (
                    {tr.duration_seconds.toFixed(2)}s)
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Observed in {tr.observations.length} sampled frames • Confidence: {(tr.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              ))}
              {doc.tracks.length === 0 && (
                <p className="text-sm text-muted-foreground col-span-2 text-center py-8">
                  No continuous moving objects tracked in this video.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

/** Audio Intelligence View Component for DocuMind AI. */

import React, { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Clock,
  Download,
  FileText,
  Languages,
  Loader2,
  Mic,
  Music,
  Pause,
  Play,
  Search,
  Sparkles,
  Users,
  Volume2,
  VolumeX,
} from "lucide-react";
import { api } from "@/services/api";
import {
  AudioDocument,
  AudioEvent,
  AudioManifest,
  AudioSegment,
  Speaker,
} from "@/types/api";

interface AudioIntelligenceViewProps {
  fileId: string;
  filename: string;
  format?: string;
}

export const AudioIntelligenceView: React.FC<AudioIntelligenceViewProps> = ({
  fileId,
  filename,
  format = "mp3",
}) => {
  const [statusLoading, setStatusLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [canonicalDoc, setCanonicalDoc] = useState<AudioDocument | null>(null);
  const [_manifest, setManifest] = useState<AudioManifest | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Audio player state
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [playbackRate, setPlaybackRate] = useState<number>(1.0);
  const [volume, setVolume] = useState<number>(1.0);
  const [isMuted, setIsMuted] = useState<boolean>(false);

  // Active view tab & search query
  const [activeTab, setActiveTab] = useState<
    "transcript" | "speakers" | "events" | "metadata"
  >("transcript");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchAudioData = async () => {
    setStatusLoading(true);
    setErrorMessage(null);
    try {
      const doc = await api.getAudioDocumentResult(fileId);
      setCanonicalDoc(doc);
    } catch {
      // Audio analysis may not have been run yet
      setCanonicalDoc(null);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchAudioData();
  }, [fileId]);

  const handleAnalyze = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzeAudioFile(fileId);
      setManifest(res);
      await fetchAudioData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze audio";
      setErrorMessage(msg);
    } finally {
      setActionLoading(false);
    }
  };

  // Audio player handlers
  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetTime = parseFloat(e.target.value);
    setCurrentTime(targetTime);
    if (audioRef.current) {
      audioRef.current.currentTime = targetTime;
    }
  };

  const seekToSegment = (startSeconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = startSeconds;
      setCurrentTime(startSeconds);
      if (!isPlaying) {
        audioRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    }
  };

  const changePlaybackRate = (rate: number) => {
    setPlaybackRate(rate);
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const newMute = !isMuted;
    setIsMuted(newMute);
    audioRef.current.muted = newMute;
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (audioRef.current) {
      audioRef.current.volume = val;
      if (val === 0) {
        setIsMuted(true);
        audioRef.current.muted = true;
      } else if (isMuted) {
        setIsMuted(false);
        audioRef.current.muted = false;
      }
    }
  };

  const formatSeconds = (sec: number): string => {
    const totalSecs = Math.max(0, Math.floor(sec));
    const mins = Math.floor(totalSecs / 60);
    const s = totalSecs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const filteredSegments: AudioSegment[] = (canonicalDoc?.segments || []).filter((seg) => {
    if (!searchQuery.trim()) return true;
    return seg.text.toLowerCase().includes(searchQuery.toLowerCase().trim());
  });

  if (statusLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-xs text-muted-foreground">Loading audio intelligence records...</p>
      </div>
    );
  }

  // Audio source URL
  const audioSourceUrl = `/api/v1/files/${encodeURIComponent(fileId)}/download`;

  return (
    <div className="space-y-4 text-xs">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={audioSourceUrl}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => setIsPlaying(false)}
        preload="metadata"
      />

      {/* Top Banner / Analysis Trigger */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 bg-card border border-border/80 rounded-xl">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-pink-500/10 text-pink-500 flex items-center justify-center shrink-0">
            <Music className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground text-sm">{filename}</span>
              <span className="rounded bg-pink-500/10 px-2 py-0.5 text-[10px] font-medium text-pink-500 uppercase">
                {format}
              </span>
              {canonicalDoc?.language && (
                <span className="rounded bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-500 uppercase flex items-center gap-1">
                  <Languages className="h-3 w-3" />
                  {canonicalDoc.language}
                </span>
              )}
            </div>
            <p className="text-[11px] text-muted-foreground">
              {canonicalDoc
                ? `${formatSeconds(canonicalDoc.duration)} duration • ${canonicalDoc.channels === 1 ? "Mono" : "Stereo"} • ${canonicalDoc.sample_rate} Hz • ${canonicalDoc.model_information.model_name}`
                : "Audio ready for multi-signal speech-to-text intelligence."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {!canonicalDoc ? (
            <button
              onClick={handleAnalyze}
              disabled={actionLoading}
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary/90 transition disabled:opacity-50 w-full sm:w-auto"
            >
              {actionLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Transcribing...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  Transcribe & Diarize
                </>
              )}
            </button>
          ) : (
            <div className="flex items-center gap-1.5 flex-wrap">
              {(["srt", "vtt", "md", "txt", "json"] as const).map((fmt) => (
                <a
                  key={fmt}
                  href={api.getAudioExportUrl(fileId, fmt)}
                  download
                  className="flex items-center gap-1 px-2.5 py-1 bg-muted/60 hover:bg-muted text-foreground border border-border/60 rounded-md text-[11px] font-medium transition"
                  title={`Export transcript as ${fmt.toUpperCase()}`}
                >
                  <Download className="h-3 w-3 text-muted-foreground" />
                  {fmt.toUpperCase()}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg text-xs">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {canonicalDoc && (
        <>
          {/* Audio Player Controls */}
          <div className="p-3.5 bg-card border border-border/80 rounded-xl space-y-2.5">
            <div className="flex items-center gap-3">
              {/* Play / Pause */}
              <button
                onClick={togglePlay}
                className="h-9 w-9 rounded-full bg-primary text-white flex items-center justify-center shrink-0 hover:bg-primary/90 transition shadow-sm"
                aria-label={isPlaying ? "Pause" : "Play"}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
              </button>

              {/* Seek Bar */}
              <div className="flex-1 flex flex-col justify-center">
                <input
                  type="range"
                  min={0}
                  max={canonicalDoc.duration || 100}
                  step={0.1}
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between items-center text-[10px] text-muted-foreground mt-1 font-mono">
                  <span>{formatSeconds(currentTime)}</span>
                  <span>{formatSeconds(canonicalDoc.duration)}</span>
                </div>
              </div>

              {/* Playback Speed Controls */}
              <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-lg border border-border/40">
                {[0.75, 1.0, 1.25, 1.5, 2.0].map((rate) => (
                  <button
                    key={rate}
                    onClick={() => changePlaybackRate(rate)}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition ${
                      playbackRate === rate
                        ? "bg-card text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {rate}x
                  </button>
                ))}
              </div>

              {/* Volume & Mute */}
              <div className="hidden sm:flex items-center gap-1.5 pl-2 border-l border-border/60">
                <button
                  onClick={toggleMute}
                  className="text-muted-foreground hover:text-foreground p-1"
                  aria-label={isMuted ? "Unmute" : "Mute"}
                >
                  {isMuted || volume === 0 ? (
                    <VolumeX className="h-4 w-4" />
                  ) : (
                    <Volume2 className="h-4 w-4" />
                  )}
                </button>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="w-14 h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center justify-between border-b border-border/80 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("transcript")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  activeTab === "transcript"
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                Transcript ({canonicalDoc.segments.length})
              </button>
              <button
                onClick={() => setActiveTab("speakers")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  activeTab === "speakers"
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                <Users className="h-3.5 w-3.5" />
                Speakers ({canonicalDoc.speakers.length})
              </button>
              <button
                onClick={() => setActiveTab("events")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  activeTab === "events"
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                <Mic className="h-3.5 w-3.5" />
                Sound Events ({canonicalDoc.events.length})
              </button>
              <button
                onClick={() => setActiveTab("metadata")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  activeTab === "metadata"
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                <Clock className="h-3.5 w-3.5" />
                Acoustic Metadata
              </button>
            </div>

            {activeTab === "transcript" && (
              <div className="relative w-48 sm:w-64">
                <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search transcript..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-md border border-border/80 bg-background pl-8 pr-2.5 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            )}
          </div>

          {/* Sub-View Content */}
          {activeTab === "transcript" && (
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {filteredSegments.length === 0 ? (
                <div className="p-8 text-center bg-card border border-border/60 rounded-xl text-muted-foreground">
                  <p>No matching transcript segments found.</p>
                </div>
              ) : (
                filteredSegments.map((seg) => {
                  const isCurrent =
                    currentTime >= seg.start && currentTime <= Math.max(seg.end, seg.start + 0.5);
                  return (
                    <div
                      key={seg.segment_id}
                      onClick={() => seekToSegment(seg.start)}
                      className={`p-3 rounded-lg border transition cursor-pointer flex flex-col gap-1.5 ${
                        isCurrent
                          ? "bg-primary/10 border-primary shadow-sm"
                          : "bg-card border-border/60 hover:border-border hover:bg-muted/30"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {seg.speaker_id && (
                            <span className="font-semibold text-primary text-[11px] px-1.5 py-0.5 rounded bg-primary/10">
                              {seg.speaker_id}
                            </span>
                          )}
                          <span className="font-mono text-[10px] text-muted-foreground">
                            {formatSeconds(seg.start)} – {formatSeconds(seg.end)}
                          </span>
                        </div>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {Math.round(seg.confidence * 100)}% conf
                        </span>
                      </div>
                      <p className="text-foreground text-xs leading-relaxed font-sans select-text">
                        {seg.text}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {activeTab === "speakers" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {canonicalDoc.speakers.map((spk: Speaker) => (
                <div
                  key={spk.speaker_id}
                  className="p-3.5 bg-card border border-border/80 rounded-xl space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-foreground">{spk.label}</span>
                    <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                      {spk.segment_ids.length} turn(s)
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground space-y-1">
                    <div>
                      Speaking Duration:{" "}
                      <span className="font-mono font-medium text-foreground">
                        {formatSeconds(spk.total_speaking_time_seconds)} (
                        {Math.round((spk.total_speaking_time_seconds / (canonicalDoc.duration || 1)) * 100)}
                        %)
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "events" && (
            <div className="space-y-2">
              {canonicalDoc.events.length === 0 ? (
                <div className="p-8 text-center bg-card border border-border/60 rounded-xl text-muted-foreground">
                  <p>No non-speech sound events detected.</p>
                </div>
              ) : (
                canonicalDoc.events.map((ev: AudioEvent) => (
                  <div
                    key={ev.event_id}
                    onClick={() => seekToSegment(ev.start)}
                    className="p-3 bg-card border border-border/60 hover:border-primary/60 rounded-lg cursor-pointer flex items-center justify-between transition"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground">{ev.category}</span>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {formatSeconds(ev.start)} – {formatSeconds(ev.end)}
                      </span>
                    </div>
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {Math.round(ev.confidence * 100)}% conf
                    </span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "metadata" && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-card border border-border/60 rounded-lg">
                <span className="text-muted-foreground block text-[10px]">Codec</span>
                <span className="font-medium text-foreground uppercase">{canonicalDoc.codec}</span>
              </div>
              <div className="p-3 bg-card border border-border/60 rounded-lg">
                <span className="text-muted-foreground block text-[10px]">Sample Rate</span>
                <span className="font-mono text-foreground">{canonicalDoc.sample_rate} Hz</span>
              </div>
              <div className="p-3 bg-card border border-border/60 rounded-lg">
                <span className="text-muted-foreground block text-[10px]">Channels</span>
                <span className="font-medium text-foreground">
                  {canonicalDoc.channels === 1 ? "1 (Mono)" : "2 (Stereo)"}
                </span>
              </div>
              <div className="p-3 bg-card border border-border/60 rounded-lg">
                <span className="text-muted-foreground block text-[10px]">Engine</span>
                <span className="font-medium text-foreground">
                  {canonicalDoc.model_information.engine_name}
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

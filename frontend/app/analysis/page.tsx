"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
  Position,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import {
  ArrowLeft,
  Clock,
  AlertTriangle,
  ShieldAlert,
  FileText,
  Layers,
  GitBranch,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const LAYER_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  schema: { bg: "#fff1f1", border: "#da1e28", text: "#a2191f", dot: "#da1e28" },
  backend: { bg: "#edf5ff", border: "#0f62fe", text: "#0043ce", dot: "#0f62fe" },
  frontend: { bg: "#defbe6", border: "#24a148", text: "#0e6027", dot: "#24a148" },
  tests: { bg: "#fcf4d6", border: "#f1c21b", text: "#8e6a00", dot: "#f1c21b" },
  config: { bg: "#f4f4f4", border: "#525252", text: "#262626", dot: "#525252" },
  docs: { bg: "#e8daff", border: "#8a3ffc", text: "#491d8b", dot: "#8a3ffc" },
  mixed: { bg: "#f4f4f4", border: "#525252", text: "#262626", dot: "#525252" },
  unknown: { bg: "#f4f4f4", border: "#a8a8a8", text: "#525252", dot: "#a8a8a8" },
};

const RISK_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  low: { bg: "bg-green-50 border-green-200", text: "text-green-800", label: "Low risk" },
  medium: { bg: "bg-yellow-50 border-yellow-200", text: "text-yellow-800", label: "Medium risk" },
  high: { bg: "bg-red-50 border-red-200", text: "text-red-800", label: "High risk" },
};

interface SubPR {
  id: string;
  suggested_title: string;
  files: string[];
  merge_order: number;
  rationale: string;
  risk_level: "low" | "medium" | "high";
  estimated_review_time_min: number;
  layer: string;
  size_lines: number;
  description_markdown: string;
  testing_recommendations: string[];
  potential_issues: string[];
  suggested_reviewer_profile: string;
}

interface AnalysisResult {
  pr_url: string;
  pr_title: string;
  repo_full_name: string;
  total_files: number;
  total_additions: number;
  total_deletions: number;
  sub_prs: SubPR[];
  graph_nodes: Array<{ id: string; data: { label?: string; layer?: string; full_path?: string }; position: { x: number; y: number } }>;
  graph_edges: Array<{ id: string; source: string; target: string }>;
  analysis_duration_ms: number;
}

function layoutNodes(
  rawNodes: AnalysisResult["graph_nodes"],
  rawEdges: AnalysisResult["graph_edges"],
  subPRs: SubPR[]
): { nodes: Node[]; edges: Edge[] } {
  // Group nodes by sub-PR
  const fileToSubPR = new Map<string, SubPR>();
  for (const sp of subPRs) {
    for (const file of sp.files) fileToSubPR.set(file, sp);
  }

  // Sort sub-PRs by merge_order
  const sortedSubPRs = [...subPRs].sort((a, b) => a.merge_order - b.merge_order);

  const subPRWidth = 280;
  const subPRGap = 60;
  const nodeHeight = 38;
  const nodeGap = 8;
  const headerHeight = 50;

  const nodes: Node[] = [];

  sortedSubPRs.forEach((sp, colIdx) => {
    const x = colIdx * (subPRWidth + subPRGap);
    const color = LAYER_COLORS[sp.layer] || LAYER_COLORS.unknown;

    // Container/group node
    nodes.push({
      id: `group-${sp.id}`,
      type: "default",
      position: { x, y: 0 },
      data: {
        label: (
          <div className="text-left p-1">
            <div className="text-[10px] font-mono uppercase tracking-wider opacity-70">
              Sub-PR #{sp.merge_order} · {sp.layer}
            </div>
            <div className="text-xs font-semibold truncate" title={sp.suggested_title}>
              {sp.suggested_title}
            </div>
          </div>
        ),
      },
      style: {
        width: subPRWidth,
        height: headerHeight + sp.files.length * (nodeHeight + nodeGap) + 16,
        background: color.bg,
        border: `2px solid ${color.border}`,
        borderRadius: 8,
        padding: 8,
        color: color.text,
        fontSize: 12,
      },
      selectable: false,
      draggable: false,
    });

    sp.files.forEach((file, fileIdx) => {
      const filename = file.split("/").pop() || file;
      nodes.push({
        id: file,
        type: "default",
        position: { x: x + 8, y: headerHeight + fileIdx * (nodeHeight + nodeGap) },
        data: {
          label: (
            <div className="text-left">
              <div className="text-[11px] font-mono truncate" title={file}>
                {filename}
              </div>
              <div className="text-[9px] text-gray-500 truncate" title={file}>
                {file.length > 32 ? "…" + file.slice(-32) : file}
              </div>
            </div>
          ),
        },
        style: {
          width: subPRWidth - 16,
          height: nodeHeight,
          background: "white",
          border: `1px solid ${color.border}40`,
          borderRadius: 4,
          padding: "4px 8px",
          fontSize: 11,
          textAlign: "left",
        },
        parentNode: `group-${sp.id}`,
        extent: "parent",
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
    });
  });

  const edges: Edge[] = rawEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "smoothstep",
    animated: false,
    style: { stroke: "#0f62fe", strokeWidth: 1.5, opacity: 0.6 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#0f62fe",
      width: 12,
      height: 12,
    },
  }));

  return { nodes, edges };
}

export default function AnalysisPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [selectedSubPR, setSelectedSubPR] = useState<SubPR | null>(null);
  const [expandedDescription, setExpandedDescription] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("pr-surgeon-analysis");
    if (!stored) {
      router.push("/");
      return;
    }
    try {
      const parsed = JSON.parse(stored) as AnalysisResult;
      setData(parsed);
      if (parsed.sub_prs.length > 0) setSelectedSubPR(parsed.sub_prs[0]);
    } catch {
      router.push("/");
    }
  }, [router]);

  const layoutResult = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };
    return layoutNodes(data.graph_nodes, data.graph_edges, data.sub_prs);
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    setNodes(layoutResult.nodes);
    setEdges(layoutResult.edges);
  }, [layoutResult, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (!data) return;
      // If clicked on a group node
      if (node.id.startsWith("group-")) {
        const subPRId = node.id.replace("group-", "");
        const sp = data.sub_prs.find((s) => s.id === subPRId);
        if (sp) setSelectedSubPR(sp);
      } else {
        // Find which sub-PR contains this file
        const sp = data.sub_prs.find((s) => s.files.includes(node.id));
        if (sp) setSelectedSubPR(sp);
      }
    },
    [data]
  );

  if (!data) {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-gray-500 text-sm">Loading analysis…</div>
      </main>
    );
  }

  const layerCounts: Record<string, number> = {};
  for (const sp of data.sub_prs) {
    layerCounts[sp.layer] = (layerCounts[sp.layer] || 0) + 1;
  }

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 shrink-0">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-ibm-blue hover:bg-blue-50 rounded transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              New analysis
            </button>
            <div className="h-6 w-px bg-gray-200" />
            <div className="min-w-0">
              <div className="text-xs text-gray-500 font-mono truncate">
                {data.repo_full_name}
              </div>
              <div className="text-sm font-semibold text-gray-900 truncate" title={data.pr_title}>
                {data.pr_title}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm shrink-0">
            <div className="flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-gray-400" />
              <span className="font-mono text-gray-900">{data.total_files}</span>
              <span className="text-gray-500 text-xs">files</span>
            </div>
            <div className="flex items-center gap-1.5">
              <GitBranch className="w-4 h-4 text-gray-400" />
              <span className="font-mono text-gray-900">{data.sub_prs.length}</span>
              <span className="text-gray-500 text-xs">sub-PRs</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-gray-400" />
              <span className="font-mono text-gray-900">{Object.keys(layerCounts).length}</span>
              <span className="text-gray-500 text-xs">layers</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-ibm-blue" />
              <span className="font-mono text-ibm-blue-dark text-xs">
                {data.analysis_duration_ms}ms
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph */}
        <div className="flex-1 relative bg-white">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            minZoom={0.2}
            maxZoom={2}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={true}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#0f62fe" gap={32} size={1} style={{ opacity: 0.06 }} />
            <Controls showInteractive={false} />
            <MiniMap
              nodeColor={(n) => {
                if (n.id.startsWith("group-")) return "#0f62fe";
                return "#a8a8a8";
              }}
              pannable
              zoomable
            />
          </ReactFlow>

          {/* Legend */}
          <div className="absolute top-3 left-3 bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm">
            <div className="text-[10px] font-medium uppercase tracking-wider text-gray-500 mb-1.5">
              Layers
            </div>
            <div className="flex items-center gap-3 text-xs">
              {Object.entries(layerCounts).map(([layer, count]) => {
                const c = LAYER_COLORS[layer] || LAYER_COLORS.unknown;
                return (
                  <div key={layer} className="flex items-center gap-1.5">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: c.dot }}
                    />
                    <span className="text-gray-700">{layer}</span>
                    <span className="text-gray-400 font-mono text-[10px]">
                      ({count})
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="w-[420px] bg-white border-l border-gray-200 flex flex-col shrink-0">
          {/* Sub-PR list */}
          <div className="border-b border-gray-200 max-h-[40%] overflow-y-auto">
            <div className="sticky top-0 bg-white px-4 py-2 border-b border-gray-100">
              <div className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Proposed sub-PRs · merge order
              </div>
            </div>
            <div>
              {data.sub_prs.map((sp) => {
                const c = LAYER_COLORS[sp.layer] || LAYER_COLORS.unknown;
                const isSelected = selectedSubPR?.id === sp.id;
                return (
                  <button
                    key={sp.id}
                    onClick={() => {
                      setSelectedSubPR(sp);
                      setExpandedDescription(false);
                    }}
                    className={`w-full text-left px-4 py-3 border-l-2 transition-colors ${
                      isSelected
                        ? "bg-blue-50 border-l-ibm-blue"
                        : "border-l-transparent hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div
                        className="flex items-center justify-center w-7 h-7 rounded-md text-[11px] font-bold shrink-0 mt-0.5"
                        style={{
                          background: c.dot,
                          color: "white",
                        }}
                      >
                        {sp.merge_order}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {sp.suggested_title}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-500">
                          <span className="font-mono">{sp.files.length} files</span>
                          <span>·</span>
                          <span className="font-mono">~{sp.estimated_review_time_min}min</span>
                          <span>·</span>
                          <span
                            className={`text-xs ${
                              sp.risk_level === "high"
                                ? "text-red-600"
                                : sp.risk_level === "medium"
                                ? "text-yellow-700"
                                : "text-green-700"
                            }`}
                          >
                            {sp.risk_level}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Selected sub-PR detail */}
          {selectedSubPR && (
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mb-4">
                <div className="text-[10px] font-mono uppercase tracking-wider text-gray-500 mb-1">
                  Sub-PR #{selectedSubPR.merge_order} · {selectedSubPR.layer}
                </div>
                <h2 className="text-base font-semibold text-gray-900 leading-snug">
                  {selectedSubPR.suggested_title}
                </h2>
              </div>

              {/* Risk pill */}
              <div
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium ${
                  RISK_STYLES[selectedSubPR.risk_level].bg
                } ${RISK_STYLES[selectedSubPR.risk_level].text}`}
              >
                {selectedSubPR.risk_level === "high" ? (
                  <ShieldAlert className="w-3.5 h-3.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5" />
                )}
                {RISK_STYLES[selectedSubPR.risk_level].label}
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-3 gap-2 mt-4">
                <div className="bg-gray-50 rounded-md p-2">
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider">
                    Files
                  </div>
                  <div className="text-lg font-semibold text-gray-900 font-mono">
                    {selectedSubPR.files.length}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-md p-2">
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider">
                    Review
                  </div>
                  <div className="text-lg font-semibold text-gray-900 font-mono flex items-baseline gap-0.5">
                    {selectedSubPR.estimated_review_time_min}
                    <span className="text-xs text-gray-500">min</span>
                  </div>
                </div>
                <div className="bg-gray-50 rounded-md p-2">
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider">
                    Lines
                  </div>
                  <div className="text-lg font-semibold text-gray-900 font-mono">
                    {selectedSubPR.size_lines}
                  </div>
                </div>
              </div>

              {/* Reviewer */}
              <div className="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-md">
                <div className="text-[10px] font-medium uppercase tracking-wider text-ibm-blue-dark mb-1">
                  Suggested reviewer
                </div>
                <div className="text-sm text-gray-900">
                  {selectedSubPR.suggested_reviewer_profile}
                </div>
              </div>

              {/* Files list */}
              <div className="mt-4">
                <div className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-2">
                  Files ({selectedSubPR.files.length})
                </div>
                <div className="space-y-1">
                  {selectedSubPR.files.slice(0, 8).map((f) => (
                    <div
                      key={f}
                      className="text-xs font-mono text-gray-700 px-2 py-1 bg-gray-50 rounded border border-gray-100 truncate"
                      title={f}
                    >
                      {f}
                    </div>
                  ))}
                  {selectedSubPR.files.length > 8 && (
                    <div className="text-xs text-gray-500 px-2">
                      + {selectedSubPR.files.length - 8} more
                    </div>
                  )}
                </div>
              </div>

              {/* Testing */}
              {selectedSubPR.testing_recommendations.length > 0 && (
                <div className="mt-4">
                  <div className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-2">
                    Testing recommendations
                  </div>
                  <ul className="space-y-1.5">
                    {selectedSubPR.testing_recommendations.map((t, i) => (
                      <li key={i} className="text-sm text-gray-700 flex gap-2">
                        <span className="text-ibm-blue shrink-0">▸</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Potential issues */}
              {selectedSubPR.potential_issues.length > 0 && (
                <div className="mt-4">
                  <div className="text-xs font-medium uppercase tracking-wider text-red-600 mb-2 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Potential issues
                  </div>
                  <ul className="space-y-1.5">
                    {selectedSubPR.potential_issues.map((t, i) => (
                      <li key={i} className="text-sm text-gray-700 flex gap-2">
                        <span className="text-red-500 shrink-0">▸</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Description toggle */}
              <div className="mt-4">
                <button
                  onClick={() => setExpandedDescription(!expandedDescription)}
                  className="flex items-center gap-1 text-xs font-medium text-ibm-blue hover:text-ibm-blue-dark"
                >
                  {expandedDescription ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                  Full PR description
                </button>
                {expandedDescription && (
                  <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 whitespace-pre-wrap font-mono">
                    {selectedSubPR.description_markdown}
                  </div>
                )}
              </div>

              {/* Rationale */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-gray-500 mb-1">
                  <Clock className="w-3 h-3" />
                  Rationale
                </div>
                <div className="text-xs text-gray-600 leading-relaxed">
                  {selectedSubPR.rationale}
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

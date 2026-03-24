"use client";

import { useState, useCallback, useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  useReactFlow,
  ReactFlowProvider,
  BackgroundVariant
} from "reactflow";
import "reactflow/dist/style.css";
import axios from "axios";

// This tells the app to use the cloud URL if it exists, otherwise fallback to local!
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Message = { role: "user" | "agent"; content: string };

const COLOR_MAP: Record<string, string> = {
  customer: "#10b981",
  order: "#3b82f6",
  product: "#f59e0b",
  material: "#f59e0b",
  plant: "#8b5cf6",
  delivery: "#ec4899",
  invoice: "#ef4444",
  payment: "#06b6d4",
  journal: "#6366f1",
  default: "#94a3b8"
};

function GraphDashboard() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "agent", content: "Hi! I can help you analyze the SAP Order-to-Cash process. Ask me to trace relations or find documents." }
  ]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);

  const { fitView, getNodes, setCenter } = useReactFlow();

  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNodeData(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeData(null);
  }, []);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Updated to use dynamic URL
        const res = await axios.get(`${API_BASE_URL}/initial-graph`);
        if (res.data.data && res.data.data.length > 0) {
          integrateDataToGraph(res.data.data, false);
        }
      } catch (err) {
        console.error("Initial load failed", err);
      }
    };
    loadInitialData();
  }, []);

  const getTypeColor = (key: string) => {
    const k = key.toLowerCase();
    if (k.includes("cust")) return COLOR_MAP.customer;
    if (k.includes("order")) return COLOR_MAP.order;
    if (k.includes("prod") || k.includes("mat")) return COLOR_MAP.product;
    if (k.includes("plant")) return COLOR_MAP.plant;
    if (k.includes("deliv")) return COLOR_MAP.delivery;
    if (k.includes("inv") || k.includes("bill")) return COLOR_MAP.invoice;
    if (k.includes("pay") || k.includes("clear")) return COLOR_MAP.payment;
    if (k.includes("journ") || k.includes("acc")) return COLOR_MAP.journal;
    return COLOR_MAP.default;
  };

  const integrateDataToGraph = (data: any[], shouldHighlight: boolean = true) => {
    if (!data || data.length === 0) return;

    if (shouldHighlight) {
      // Find existing nodes matching the query values
      const currentNodes = getNodes();
      const foundNodes: Node[] = [];
      data.forEach((row) => {
        Object.values(row).forEach((val) => {
          if (val === null || val === undefined) return;
          const strVal = String(val);
          const match = currentNodes.find(n => n.data && n.data.label === strVal);
          if (match && !foundNodes.find(n => n.id === match.id)) {
            foundNodes.push(match);
          }
        });
      });

      if (foundNodes.length > 0) {
        setSelectedNodeData(foundNodes[0]);
        setTimeout(() => {
          fitView({ nodes: foundNodes, duration: 1500, padding: 0.2, maxZoom: 1.2 });
        }, 100);
      }
      return; // Exit here. DO NOT modify nodes/edges visually.
    }

    // --- INITIAL GRAPH LOAD ONLY ---
    setNodes((prevNodes) => {
      let updatedNodes = [...prevNodes];

      data.forEach((row) => {
        const keys = Object.keys(row);
        const rowNodeIds: string[] = [];

        keys.forEach((key) => {
          const val = row[key];
          if (val === null || val === undefined) return;

          const nodeId = `${key}-${val}`;
          rowNodeIds.push(nodeId);

          if (!updatedNodes.find((n) => n.id === nodeId)) {
            // Zone-based spreading with medium area
            let yPos = (Math.random() * 2000) - 1000;
            let xPos = 0;
            const type = key.toLowerCase();

            if (type.includes("cust")) xPos = (Math.random() * 500) - 1000;
            else if (type.includes("order")) xPos = 500 + (Math.random() * 1000);
            else if (type.includes("prod") || type.includes("mat")) xPos = 2000 + (Math.random() * 1000);
            else if (type.includes("deliv") || type.includes("plant")) xPos = 3500 + (Math.random() * 1000);
            else if (type.includes("inv") || type.includes("bill")) xPos = 5000 + (Math.random() * 1000);
            else xPos = 6500 + (Math.random() * 2000);

            updatedNodes.push({
              id: nodeId,
              position: { x: xPos, y: yPos },
              data: { label: String(val), metadata: row, type: key },
              style: {
                background: getTypeColor(key),
                color: "#fff",
                borderRadius: "50%",
                width: 55,
                height: 55,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                fontSize: "9px",
                fontWeight: "bold",
                border: "2px solid rgba(255,255,255,0.4)",
                transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)"
              }
            });
          }
        });

        for (let i = 0; i < rowNodeIds.length - 1; i++) {
          const source = rowNodeIds[i];
          const target = rowNodeIds[i + 1];
          const edgeId = `e-${source}-${target}`;

          setEdges((prevEdges) => {
            if (!prevEdges.find((e) => e.id === edgeId)) {
              return [...prevEdges, {
                id: edgeId,
                source,
                target,
                animated: false,
                style: { stroke: "#cbd5e1", strokeWidth: 2, transition: "all 0.4s" }
              }];
            }
            return prevEdges;
          });
        }
      });
      return updatedNodes;
    });

    setTimeout(() => fitView({ duration: 1000, padding: 0.2 }), 200);
  };

  const handleSend = async () => {
    if (!prompt.trim()) return;
    const userMsg = prompt;
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setPrompt("");
    setLoading(true);

    try {
      // Updated to use dynamic URL
      const res = await axios.post(`${API_BASE_URL}/query`, { message: userMsg });
      setMessages((prev) => [...prev, { role: "agent", content: res.data.explanation }]);
      integrateDataToGraph(res.data.data, true);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "agent", content: "⚠️ System error: Connection failed." }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen w-screen bg-white font-sans text-gray-900 overflow-hidden">
      <div className="flex-1 relative bg-[#f8fafc]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          fitView
          // SMOOTHNESS SETTINGS
          zoomOnScroll={true}
          panOnScroll={false}
          panOnDrag={true}
          elementsSelectable={true}
        >
          <Background color="#e2e8f0" gap={20} variant={BackgroundVariant.Dots} />
          <Controls />
        </ReactFlow>

        {selectedNodeData && (
          <div className="absolute top-10 left-10 bg-white shadow-2xl rounded-2xl p-6 border border-slate-100 w-80 z-50 animate-in fade-in zoom-in duration-300">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-black text-slate-800 capitalize leading-tight">
                {selectedNodeData.data.type}
              </h3>
              <div className="px-2 py-1 rounded bg-slate-100 text-[9px] font-bold text-slate-500 uppercase">Details</div>
            </div>
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
              {Object.entries(selectedNodeData.data.metadata).map(([key, value]) => (
                <div key={key} className="border-b border-slate-50 pb-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">{key}</span>
                  <span className="text-sm text-slate-700 font-semibold break-words">{String(value)}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => setSelectedNodeData(null)}
              className="mt-6 w-full bg-slate-900 hover:bg-black text-white py-3 rounded-xl font-bold text-xs transition-all shadow-lg"
            >
              DISMISS
            </button>
          </div>
        )}
      </div>

      <div className="w-[400px] flex flex-col bg-white border-l border-slate-200 shadow-2xl z-10">
        <div className="p-6 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-indigo-200 shadow-lg">
              <span className="text-white font-black text-xl">D</span>
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-800 tracking-tighter">DodgeAI</h2>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Postgres Engine Active</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
              <span className="text-[10px] font-black text-slate-300 uppercase mb-2 tracking-widest">
                {msg.role === "agent" ? "System Agent" : "Authorized User"}
              </span>
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap ${msg.role === "user"
                  ? "bg-slate-900 text-white rounded-tr-none"
                  : "bg-slate-100 text-slate-800 border border-slate-200 rounded-tl-none"
                  }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex flex-col gap-2 animate-pulse">
              <div className="h-4 w-20 bg-slate-100 rounded"></div>
              <div className="h-12 w-full bg-slate-50 rounded-2xl"></div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-100">
          <div className="relative">
            <textarea
              className="w-full p-4 pr-16 text-sm bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent focus:outline-none transition-all resize-none font-medium"
              rows={3}
              placeholder="Ask for relations, e.g. 'Hawkins Ltd to Order 740546'..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !prompt.trim()}
              className="absolute bottom-4 right-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white p-2.5 rounded-xl transition-all shadow-lg shadow-indigo-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <GraphDashboard />
    </ReactFlowProvider>
  );
}
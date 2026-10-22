import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ArrowRight,
  Bot,
  Brain,
  MessageSquare,
  Database,
  Settings,
  Zap,
  CheckCircle2,
  ExternalLink,
  FileText,
  Search,
  Clock,
  Shield,
  Smartphone,
} from 'lucide-react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Moltbot for GTM Agents | Persistent Memory AI Assistant | GTM Skills',
  description: 'How to use Moltbot (formerly Clawdbot) to build GTM agents with persistent memory. Learn about memory systems, session management, and multi-channel sales workflows.',
  keywords: 'moltbot, clawdbot, ai memory, persistent memory, gtm agents, sales ai, whatsapp ai, telegram bot, sales automation',
};

const memoryFeatures = [
  {
    title: 'Markdown-Based Storage',
    description: 'Memory stored as plain Markdown files in your workspace. No proprietary formats. Readable, editable, portable.',
    icon: FileText,
  },
  {
    title: 'Daily Logs + Long-Term Memory',
    description: 'Two-layer system: daily notes (memory/YYYY-MM-DD.md) for context, MEMORY.md for durable facts about prospects.',
    icon: Database,
  },
  {
    title: 'Semantic Search',
    description: 'Vector embeddings + BM25 hybrid search. Find relevant context even when wording differs.',
    icon: Search,
  },
  {
    title: 'Auto Memory Flush',
    description: 'Before context compaction, Moltbot automatically prompts the model to save important memories.',
    icon: Brain,
  },
];

const gtmUseCases = [
  {
    title: 'Prospect Memory',
    description: 'Store everything about a prospect: company context, pain points, past conversations, decision timeline. Never ask the same question twice.',
    example: 'MEMORY.md entry: "John @ Acme - Series B, hiring 3 AEs, evaluated competitor in Q3, budget cycle is January"',
  },
  {
    title: 'Multi-Channel Continuity',
    description: 'Start conversation on WhatsApp, continue on Telegram, reference context from either. Memory persists across all channels.',
    example: 'Session scope: per-sender means John\'s context follows him regardless of channel.',
  },
  {
    title: 'Deal Stage Tracking',
    description: 'Agent remembers where each deal is, what was discussed, what objections were raised, what next steps were agreed.',
    example: 'Daily log: "2024-01-29: Called John, discussed pricing, he needs to loop in CFO, follow up Thursday"',
  },
  {
    title: 'Personalization at Scale',
    description: 'With persistent memory per prospect, every interaction is contextual. No more "Hi {first_name}" generic outreach.',
    example: 'Agent recalls: "John mentioned they use Salesforce + Outreach, struggling with data quality"',
  },
];

const configHighlights = [
  {
    setting: 'session.scope',
    options: ['per-sender', 'per-channel', 'global'],
    gtmUse: 'Use per-sender for individual prospect tracking, per-channel for team shared context.',
  },
  {
    setting: 'session.reset.mode',
    options: ['daily', 'idle'],
    gtmUse: 'Daily reset clears working memory but MEMORY.md persists. Idle reset after X minutes of inactivity.',
  },
  {
    setting: 'contextPruning.mode',
    options: ['off', 'adaptive', 'aggressive'],
    gtmUse: 'Adaptive preserves important context while managing token limits. Best for long sales cycles.',
  },
  {
    setting: 'compaction.memoryFlush',
    options: ['enabled', 'disabled'],
    gtmUse: 'Enable to auto-save prospect details before context compaction. Critical for sales.',
  },
];

export default function MoltbotPage() {
  return (
    <div className="py-12 md:py-20">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="mb-12">
          <Badge variant="outline" className="mb-4 border-purple-500/30 text-purple-400">
            <Bot className="h-3 w-3 mr-1" />
            AI Infrastructure
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Moltbot for GTM Agents
          </h1>
          <p className="text-lg text-muted-foreground mb-6">
            Build sales agents with persistent memory that remember every prospect,
            every conversation, every deal detail—across WhatsApp, Telegram, Discord, and more.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="https://molt.bot" target="_blank" rel="noopener noreferrer">
              <Button className="gap-2">
                Get Moltbot
                <ExternalLink className="h-4 w-4" />
              </Button>
            </a>
            <a href="https://docs.molt.bot" target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="gap-2">
                Documentation
                <ArrowRight className="h-4 w-4" />
              </Button>
            </a>
          </div>
        </div>

        {/* What is Moltbot */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-4">What is Moltbot?</h2>
          <div className="p-6 rounded-xl bg-zinc-900/50 border border-zinc-800">
            <p className="text-muted-foreground mb-4">
              Moltbot (formerly Clawdbot) is a messaging gateway that connects WhatsApp, Telegram,
              Discord, Slack, Signal, and iMessage to AI agents like Claude. It runs locally on your
              machine with <strong>persistent memory</strong>—your agent remembers context across
              sessions, channels, and conversations.
            </p>
            <p className="text-muted-foreground">
              For GTM teams, this means building sales agents that maintain context about every
              prospect indefinitely. No more losing deal context. No more "remind me what we discussed."
              The agent knows.
            </p>
          </div>
        </section>

        {/* Why Memory Matters */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6">Why Memory Matters for Sales</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl bg-red-500/5 border border-red-500/20">
              <h3 className="font-semibold text-red-400 mb-3">Without Persistent Memory</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Every conversation starts from zero</li>
                <li>• Context lost between sessions</li>
                <li>• Can't track deals across channels</li>
                <li>• Generic, impersonal interactions</li>
                <li>• Manual note-taking required</li>
              </ul>
            </div>
            <div className="p-6 rounded-xl bg-green-500/5 border border-green-500/20">
              <h3 className="font-semibold text-green-400 mb-3">With Moltbot Memory</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Remembers every prospect detail</li>
                <li>• Context persists 24/7</li>
                <li>• Unified memory across all channels</li>
                <li>• Deeply personalized follow-ups</li>
                <li>• Automatic memory management</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Memory System Deep Dive */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Brain className="h-6 w-6 text-purple-400" />
            The Memory System
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            {memoryFeatures.map((feature) => (
              <div
                key={feature.title}
                className="p-5 rounded-xl bg-card border border-border hover:border-purple-500/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                    <feature.icon className="h-5 w-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-6 rounded-xl bg-zinc-900/50 border border-zinc-800">
            <h3 className="font-semibold mb-3">How It Works</h3>
            <div className="font-mono text-sm bg-black/50 p-4 rounded-lg overflow-x-auto">
              <pre>{`~/clawd/
├── MEMORY.md           # Long-term: prospect facts, preferences, deal details
└── memory/
    ├── 2024-01-28.md   # Yesterday's context (auto-loaded)
    └── 2024-01-29.md   # Today's notes (auto-loaded)`}</pre>
            </div>
            <p className="text-sm text-muted-foreground mt-3">
              At session start, Moltbot loads MEMORY.md + last 2 days of logs. Semantic search
              retrieves relevant chunks when needed. Before compaction, it prompts the model to
              save important memories.
            </p>
          </div>
        </section>

        {/* GTM Use Cases */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Zap className="h-6 w-6 text-orange-400" />
            GTM Use Cases
          </h2>
          <div className="space-y-4">
            {gtmUseCases.map((useCase, i) => (
              <div
                key={i}
                className="p-6 rounded-xl bg-card border border-border hover:border-orange-500/30 transition-colors"
              >
                <h3 className="font-semibold mb-2">{useCase.title}</h3>
                <p className="text-sm text-muted-foreground mb-3">{useCase.description}</p>
                <div className="font-mono text-xs bg-orange-500/5 border border-orange-500/20 p-3 rounded-lg">
                  {useCase.example}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Key Configuration */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Settings className="h-6 w-6 text-cyan-400" />
            Key Settings for Sales Agents
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium">Setting</th>
                  <th className="text-left py-3 px-4 font-medium">Options</th>
                  <th className="text-left py-3 px-4 font-medium">GTM Use</th>
                </tr>
              </thead>
              <tbody>
                {configHighlights.map((config, i) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="py-3 px-4 font-mono text-purple-400">{config.setting}</td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {config.options.map((opt) => (
                          <Badge key={opt} variant="secondary" className="text-xs">
                            {opt}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{config.gtmUse}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Multi-Channel */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <Smartphone className="h-6 w-6 text-green-400" />
            Multi-Channel Support
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['WhatsApp', 'Telegram', 'Discord', 'Slack', 'Signal', 'iMessage', 'Teams', 'Mattermost'].map((channel) => (
              <div
                key={channel}
                className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 text-center"
              >
                <div className="font-medium">{channel}</div>
              </div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            Memory persists across all channels. Start a deal conversation on WhatsApp,
            continue on Telegram, reference it from Discord—the agent remembers everything.
          </p>
        </section>

        {/* Sample Config */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6">Sample GTM Agent Config</h2>
          <div className="font-mono text-sm bg-zinc-900 border border-zinc-800 p-6 rounded-xl overflow-x-auto">
            <pre>{`// ~/.clawdbot/moltbot.json
{
  "agents": {
    "defaults": {
      "workspace": "~/sales-agent",
      "model": { "primary": "anthropic/claude-sonnet-4" },

      // Memory settings
      "contextPruning": { "mode": "adaptive" },
      "compaction": {
        "mode": "summarize",
        "memoryFlush": { "enabled": true }
      }
    }
  },

  "session": {
    "scope": "per-sender",           // Each prospect gets own context
    "reset": {
      "mode": "idle",
      "idleMinutes": 480             // Reset after 8 hours idle
    }
  },

  "channels": {
    "whatsapp": {
      "dmPolicy": "pairing",         // Approve new contacts first
      "sendReadReceipts": true
    },
    "telegram": {
      "historyLimit": 50             // Load last 50 messages for context
    }
  }
}`}</pre>
          </div>
        </section>

        {/* Getting Started */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-6">Getting Started</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
              <span className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold flex-shrink-0">1</span>
              <div>
                <h3 className="font-semibold">Install Moltbot</h3>
                <code className="text-sm text-muted-foreground">npm install -g moltbot@latest</code>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
              <span className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold flex-shrink-0">2</span>
              <div>
                <h3 className="font-semibold">Run Setup Wizard</h3>
                <code className="text-sm text-muted-foreground">moltbot onboard --install-daemon</code>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
              <span className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold flex-shrink-0">3</span>
              <div>
                <h3 className="font-semibold">Connect Channels</h3>
                <code className="text-sm text-muted-foreground">moltbot channels login</code>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
              <span className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold flex-shrink-0">4</span>
              <div>
                <h3 className="font-semibold">Configure for Sales</h3>
                <p className="text-sm text-muted-foreground">Edit ~/.clawdbot/moltbot.json with GTM-optimized settings above</p>
              </div>
            </div>
          </div>
        </section>

        {/* Related */}
        <section className="mb-16">
          <h2 className="text-xl font-bold mb-4">Related Resources</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <Link
              href="/tutorials/moltbot-agentic-sdr"
              className="p-4 rounded-lg border border-border bg-card hover:border-purple-500/30 transition-colors"
            >
              <div className="font-semibold mb-1">Build an Agentic SDR</div>
              <div className="text-sm text-muted-foreground">Full tutorial with Moltbot</div>
            </Link>
            <Link
              href="/agentic-bdr"
              className="p-4 rounded-lg border border-border bg-card hover:border-purple-500/30 transition-colors"
            >
              <div className="font-semibold mb-1">Agentic BDR Guide</div>
              <div className="text-sm text-muted-foreground">What is an AI sales agent?</div>
            </Link>
            <Link
              href="/prompts"
              className="p-4 rounded-lg border border-border bg-card hover:border-purple-500/30 transition-colors"
            >
              <div className="font-semibold mb-1">2,500+ GTM Prompts</div>
              <div className="text-sm text-muted-foreground">Prompts for your agents</div>
            </Link>
          </div>
        </section>

        {/* CTA */}
        <div className="p-8 rounded-2xl bg-gradient-to-br from-purple-500/10 via-pink-500/5 to-transparent border border-purple-500/20 text-center">
          <h2 className="text-2xl font-bold mb-4">
            Ready to Build Memory-Powered Sales Agents?
          </h2>
          <p className="text-muted-foreground mb-6 max-w-lg mx-auto">
            Moltbot + GTM Skills prompts = agents that remember everything
            about your prospects and never drop context.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="https://molt.bot" target="_blank" rel="noopener noreferrer">
              <Button className="gap-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600">
                Get Moltbot
                <ExternalLink className="h-4 w-4" />
              </Button>
            </a>
            <a href="https://docs.molt.bot" target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="gap-2">
                Read the Docs
                <ArrowRight className="h-4 w-4" />
              </Button>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

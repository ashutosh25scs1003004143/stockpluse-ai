/**
 * StockPulse AI – Understand Markets. Invest Smarter.
 * SINGLE-FILE FULL-STACK APP (Express + MongoDB + Socket.IO + Gemini + embedded React-style SPA).
 *
 * Deploy: put this file + package.json (below) in a repo.  Start command: npm start
 *
 * package.json:
 * {
 *   "name": "stockpulse-ai", "version": "1.0.0", "type": "module", "private": true,
 *   "scripts": { "start": "tsx app.ts", "dev": "tsx watch app.ts" },
 *   "engines": { "node": ">=18" },
 *   "dependencies": { "bcryptjs": "^2.4.3", "cookie": "^0.6.0", "cookie-parser": "^1.4.6", "cors": "^2.8.5",
 *     "dotenv": "^16.4.5", "express": "^4.19.2", "express-mongo-sanitize": "^2.2.0", "express-rate-limit": "^7.4.0",
 *     "helmet": "^7.1.0", "jsonwebtoken": "^9.0.2", "mongoose": "^8.5.0", "morgan": "^1.10.0",
 *     "socket.io": "^4.7.5", "tsx": "^4.16.0", "zod": "^3.23.8" }
 * }
 *
 * Env vars: MONGODB_URI, JWT_SECRET, GEMINI_API_KEY, [GEMINI_MODEL], [MARKET_PROVIDER_KEY], PORT, NODE_ENV=production
 * With no MARKET_PROVIDER_KEY the app runs in clearly-labelled DEMO MODE (fictional data).
 */
import 'dotenv/config';
import express, { Router } from 'express';
import type { NextFunction, Request, Response } from 'express';
import http from 'http';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import cookieParser from 'cookie-parser';
import cookie from 'cookie';
import mongoSanitize from 'express-mongo-sanitize';
import rateLimit from 'express-rate-limit';
import mongoose, { Schema } from 'mongoose';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import type { ZodSchema } from 'zod';
import { Server } from 'socket.io';

// ===== config/env.ts =====
const env = {
  port: Number(process.env.PORT || 4000),
  prod: process.env.NODE_ENV === 'production',
  mongo: process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/stockpulse',
  jwt: process.env.JWT_SECRET || '',
  client: process.env.CLIENT_ORIGIN || 'http://localhost:5173',
  gemini: process.env.GEMINI_API_KEY || '',
  geminiModel: process.env.GEMINI_MODEL || 'gemini-2.0-flash',
  marketKey: process.env.MARKET_PROVIDER_KEY || '',
};

if (!env.jwt) {
  if (env.prod) throw new Error('JWT_SECRET is required in production');
  env.jwt = 'dev-only-secret-not-for-production';
}

// ===== models/index.ts =====
const opts = { timestamps: true };
const ref = (m: string) => ({ type: Schema.Types.ObjectId, ref: m, required: true, index: true });

const User = mongoose.model('User', new Schema({
  name: { type: String, required: true, trim: true, maxlength: 80 },
  email: { type: String, required: true, unique: true, lowercase: true, trim: true },
  passwordHash: { type: String, required: true },
  preferences: { exchange: { type: String, enum: ['NSE', 'BSE'], default: 'NSE' } },
}, { timestamps: { createdAt: true, updatedAt: false } }));

const Stock = mongoose.model('Stock', new Schema({
  symbol: { type: String, required: true, unique: true, uppercase: true },
  companyName: { type: String, required: true },
  exchange: { type: String, enum: ['NSE', 'BSE'], required: true },
  sector: String,
}));

const Watchlist = mongoose.model('Watchlist', new Schema({
  userId: ref('User'),
  name: { type: String, required: true, maxlength: 60 },
  stockSymbols: [{ type: String, uppercase: true }],
}, opts));

const Transaction = mongoose.model('Transaction', new Schema({
  userId: ref('User'),
  symbol: { type: String, required: true, uppercase: true },
  exchange: { type: String, enum: ['NSE', 'BSE'], default: 'NSE' },
  quantity: { type: Number, required: true, min: 1 },
  price: { type: Number, required: true, min: 0.01 },
  transactionType: { type: String, enum: ['BUY', 'SELL'], required: true },
  transactionDate: { type: Date, required: true, default: Date.now },
}, opts));

const VirtualAccount = mongoose.model('VirtualAccount', new Schema({
  userId: { ...ref('User'), unique: true },
  virtualBalance: { type: Number, required: true, min: 0, default: 100000 },
}, opts));

const VirtualTrade = mongoose.model('VirtualTrade', new Schema({
  userId: ref('User'),
  symbol: { type: String, required: true, uppercase: true },
  quantity: { type: Number, required: true, min: 1 },
  price: { type: Number, required: true },
  tradeType: { type: String, enum: ['BUY', 'SELL'], required: true },
  simulated: { type: Boolean, default: true },
  timestamp: { type: Date, default: Date.now },
}));

const Alert = mongoose.model('Alert', new Schema({
  userId: ref('User'),
  symbol: { type: String, required: true, uppercase: true },
  condition: { type: String, enum: ['PRICE_ABOVE', 'PRICE_BELOW', 'PCT_UP', 'PCT_DOWN'], required: true },
  targetPrice: { type: Number, required: true },
  active: { type: Boolean, default: true, index: true },
  triggeredAt: Date,
}, opts));

const AIReport = mongoose.model('AIReport', new Schema({
  userId: ref('User'),
  symbol: String,
  analysis: Schema.Types.Mixed,
}, { timestamps: { createdAt: true, updatedAt: false } }));

const Notification = mongoose.model('Notification', new Schema({
  userId: ref('User'),
  message: String,
  read: { type: Boolean, default: false },
}, { timestamps: { createdAt: true, updatedAt: false } }));

// ===== middleware/index.ts =====
class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

const asyncH = (fn: (req: Request, res: Response) => Promise<any>) =>
  (req: Request, res: Response, next: NextFunction) => fn(req, res).catch(next);

function signToken(userId: string) {
  return jwt.sign({ sub: userId }, env.jwt, { expiresIn: '7d' });
}

function readUserId(token?: string): string | null {
  if (!token) return null;
  try { return (jwt.verify(token, env.jwt) as any).sub; } catch { return null; }
}

function requireAuth(req: Request, res: Response, next: NextFunction) {
  const id = readUserId(req.cookies?.token);
  if (!id) return next(new HttpError(401, 'Authentication required'));
  res.locals.userId = id;
  next();
}

// CSRF defence: SameSite cookie + custom header required on state-changing requests.
function csrfGuard(req: Request, _res: Response, next: NextFunction) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return next();
  if (req.get('x-requested-with') !== 'StockPulse') return next(new HttpError(403, 'CSRF check failed'));
  next();
}

const validate = (schema: ZodSchema) => (req: Request, _res: Response, next: NextFunction) => {
  const r = schema.safeParse(req.body);
  if (!r.success) return next(new HttpError(400, r.error.issues.map(i => `${i.path.join('.')}: ${i.message}`).join('; ')));
  req.body = r.data;
  next();
};

function errorHandler(err: any, _req: Request, res: Response, _next: NextFunction) {
  const status = err instanceof HttpError ? err.status : 500;
  if (status === 500) console.error(err);
  res.status(status).json({ error: status === 500 ? 'Internal server error' : err.message });
}

// ===== services/market/types.ts =====
type Exchange = 'NSE' | 'BSE';
interface Quote {
  symbol: string; name: string; exchange: Exchange; sector: string;
  price: number; change: number; changePercent: number;
  open: number; high: number; low: number; prevClose: number; volume: number;
  week52High: number; week52Low: number; marketCap: number; asOf: string;
}
interface IndexQuote {
  symbol: string; name: string; value: number; change: number; changePercent: number;
  prevClose: number; spark: number[]; asOf: string;
}
interface Candle { time: number; open: number; high: number; low: number; close: number; volume: number }
interface Fundamentals {
  pe: number | null; pb: number | null; eps: number | null; roe: number | null; roce: number | null;
  debtToEquity: number | null; revenueGrowth: number | null; profitGrowth: number | null;
  dividendYield: number | null; asOf: string;
}
type Range = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | '5Y';

/** Implement this interface to plug in any licensed NSE/BSE data vendor. */
interface MarketProvider {
  readonly name: string;
  readonly demo: boolean;
  getIndices(): Promise<IndexQuote[]>;
  getQuotes(): Promise<Quote[]>;
  getQuote(symbol: string): Promise<Quote | null>;
  getHistory(symbol: string, range: Range): Promise<Candle[]>;
  getFundamentals(symbol: string): Promise<Fundamentals | null>;
  getSessionStatus(): { open: boolean; label: string };
}

// ===== services/market/demoProvider.ts =====
// FICTIONAL companies and synthetic numbers. NOT real market data.
const UNIVERSE = [
  { symbol: 'DEMOBANK', name: 'Demo Bank Ltd (fictional)', sector: 'Banking', base: 1500, cap: 900000 },
  { symbol: 'DEMOFIN', name: 'Demo Finserve Ltd (fictional)', sector: 'Banking', base: 780, cap: 300000 },
  { symbol: 'DEMOTECH', name: 'Demo Technologies Ltd (fictional)', sector: 'IT', base: 3400, cap: 1200000 },
  { symbol: 'DEMOSOFT', name: 'Demo Softworks Ltd (fictional)', sector: 'IT', base: 1650, cap: 650000 },
  { symbol: 'DEMOMOTO', name: 'Demo Motors Ltd (fictional)', sector: 'Automobile', base: 920, cap: 340000 },
  { symbol: 'DEMOPHARMA', name: 'Demo Pharma Ltd (fictional)', sector: 'Pharma', base: 1280, cap: 310000 },
  { symbol: 'DEMOFMCG', name: 'Demo Consumer Ltd (fictional)', sector: 'FMCG', base: 2450, cap: 580000 },
  { symbol: 'DEMOPOWER', name: 'Demo Power Ltd (fictional)', sector: 'Energy', base: 310, cap: 420000 },
  { symbol: 'DEMOSTEEL', name: 'Demo Steel Ltd (fictional)', sector: 'Metal', base: 145, cap: 180000 },
  { symbol: 'DEMOREALTY', name: 'Demo Realty Ltd (fictional)', sector: 'Realty', base: 2100, cap: 90000 },
  { symbol: 'DEMOOIL', name: 'Demo Petroleum Ltd (fictional)', sector: 'Energy', base: 2900, cap: 1800000 },
  { symbol: 'DEMOCEMENT', name: 'Demo Cement Ltd (fictional)', sector: 'Metal', base: 10500, cap: 280000 },
];

const hash = (s: string) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const noise = (seed: number) => {
  let t = (seed + 0x6D2B79F5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return (((t ^ (t >>> 14)) >>> 0) / 4294967296) * 2 - 1;
};
const r2 = (n: number) => Math.round(n * 100) / 100;
const DAY = 86400000;
const dayClose = (u: typeof UNIVERSE[0], dayIdx: number) => {
  const h = hash(u.symbol);
  return u.base * (1 + 0.12 * Math.sin(dayIdx / 25 + h) + 0.02 * noise(dayIdx * 7919 + h));
};
const todayIdx = () => Math.floor(Date.now() / DAY);

class DemoProvider implements MarketProvider {
  readonly name = 'DEMO (fictional data)';
  readonly demo = true;

  private build(u: typeof UNIVERSE[0]): Quote {
    const d = todayIdx(); const h = hash(u.symbol);
    const prevClose = dayClose(u, d - 1);
    const price = dayClose(u, d) * (1 + 0.004 * Math.sin(Date.now() / 60000 + h));
    const hi = Math.max(price, prevClose) * 1.006, lo = Math.min(price, prevClose) * 0.994;
    let w52h = -Infinity, w52l = Infinity;
    for (let i = 0; i < 252; i += 3) { const c = dayClose(u, d - i); w52h = Math.max(w52h, c); w52l = Math.min(w52l, c); }
    return {
      symbol: u.symbol, name: u.name, exchange: 'NSE', sector: u.sector,
      price: r2(price), change: r2(price - prevClose), changePercent: r2(((price - prevClose) / prevClose) * 100),
      open: r2(prevClose * 1.001), high: r2(hi), low: r2(lo), prevClose: r2(prevClose),
      volume: Math.floor(500000 + Math.abs(noise(d + h)) * 4000000),
      week52High: r2(w52h), week52Low: r2(w52l), marketCap: u.cap, asOf: new Date().toISOString(),
    };
  }

  async getQuotes() { return UNIVERSE.map(u => this.build(u)); }
  async getQuote(symbol: string) {
    const u = UNIVERSE.find(x => x.symbol === symbol.toUpperCase());
    return u ? this.build(u) : null;
  }

  async getIndices(): Promise<IndexQuote[]> {
    const defs = [
      { symbol: 'NIFTY50', name: 'NIFTY 50 (demo)', base: 24500 },
      { symbol: 'SENSEX', name: 'SENSEX (demo)', base: 80500 },
      { symbol: 'BANKNIFTY', name: 'BANK NIFTY (demo)', base: 52000 },
      { symbol: 'NIFTYIT', name: 'NIFTY IT (demo)', base: 38000 },
    ];
    const d = todayIdx();
    return defs.map(x => {
      const h = hash(x.symbol);
      const f = (i: number) => x.base * (1 + 0.05 * Math.sin(i / 30 + h));
      const prevClose = f(d - 1);
      const spark = Array.from({ length: 40 }, (_, i) =>
        r2(f(d) * (1 + 0.004 * Math.sin(i / 5 + h) + 0.0015 * noise(i * 13 + h + Math.floor(Date.now() / 3600000)))));
      const value = spark[spark.length - 1];
      return { symbol: x.symbol, name: x.name, value, change: r2(value - prevClose),
        changePercent: r2(((value - prevClose) / prevClose) * 100), prevClose: r2(prevClose), spark, asOf: new Date().toISOString() };
    });
  }

  async getHistory(symbol: string, range: Range): Promise<Candle[]> {
    const u = UNIVERSE.find(x => x.symbol === symbol.toUpperCase());
    if (!u) return [];
    const h = hash(u.symbol);
    const days: Record<Range, number> = { '1D': 1, '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '5Y': 1825 };
    const out: Candle[] = [];
    if (range === '1D') {
      const start = Math.floor(Date.now() / DAY) * DAY + 3.75 * 3600000;
      const base = dayClose(u, todayIdx() - 1);
      for (let i = 0; i < 75; i++) {
        const o = base * (1 + 0.004 * Math.sin(i / 8 + h) + 0.001 * noise(i + h));
        const c = base * (1 + 0.004 * Math.sin((i + 1) / 8 + h) + 0.001 * noise(i + 1 + h));
        out.push({ time: Math.floor((start + i * 300000) / 1000), open: r2(o), high: r2(Math.max(o, c) * 1.001), low: r2(Math.min(o, c) * 0.999), close: r2(c), volume: Math.floor(20000 + Math.abs(noise(i + h)) * 90000) });
      }
      return out;
    }
    const d = todayIdx();
    for (let i = days[range]; i >= 0; i--) {
      const idx = d - i;
      const o = dayClose(u, idx - 1), c = dayClose(u, idx);
      out.push({ time: Math.floor((idx * DAY) / 1000), open: r2(o), high: r2(Math.max(o, c) * (1 + 0.006 * Math.abs(noise(idx + h)))),
        low: r2(Math.min(o, c) * (1 - 0.006 * Math.abs(noise(idx * 3 + h)))), close: r2(c), volume: Math.floor(500000 + Math.abs(noise(idx + h)) * 4000000) });
    }
    return out;
  }

  async getFundamentals(symbol: string): Promise<Fundamentals | null> {
    const u = UNIVERSE.find(x => x.symbol === symbol.toUpperCase());
    if (!u) return null;
    const h = hash(u.symbol);
    const n = (k: number, lo: number, hi: number) => r2(lo + ((noise(h + k) + 1) / 2) * (hi - lo));
    return { pe: n(1, 12, 38), pb: n(2, 1.5, 8), eps: n(3, 10, 120), roe: n(4, 8, 28), roce: n(5, 9, 30),
      debtToEquity: n(6, 0, 1.4), revenueGrowth: n(7, -3, 22), profitGrowth: n(8, -8, 30), dividendYield: n(9, 0, 3), asOf: new Date().toISOString() };
  }

  getSessionStatus() {
    const ist = new Date(Date.now() + 5.5 * 3600000);
    const mins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
    const wd = ist.getUTCDay();
    const open = wd >= 1 && wd <= 5 && mins >= 9 * 60 + 15 && mins <= 15 * 60 + 30;
    return { open, label: open ? 'Market Open' : 'Market Closed' };
  }
}

// ===== integrations/liveProvider.ts =====
/**
 * TEMPLATE for a licensed NSE/BSE data vendor (broker API or data licensee).
 * Implement each method with the vendor's REST/WebSocket API using env.marketKey.
 * Do NOT scrape exchange websites. Check the vendor's redistribution terms.
 */
class LiveProvider implements MarketProvider {
  readonly name = 'LIVE (configure vendor)';
  readonly demo = false;
  private nope(): never { throw new Error(`LiveProvider not implemented. Fill integrations/liveProvider.ts (key set: ${!!env.marketKey}).`); }
  getIndices() { return this.nope(); }
  getQuotes() { return this.nope(); }
  getQuote(_s: string) { return this.nope(); }
  getHistory(_s: string, _r: any) { return this.nope(); }
  getFundamentals(_s: string) { return this.nope(); }
  getSessionStatus() { return { open: false, label: 'Unknown' }; }
}

// ===== services/market/marketService.ts =====
const provider: MarketProvider = env.marketKey ? new LiveProvider() : new DemoProvider();

const cache = new Map<string, { exp: number; val: any }>();
async function cached<T>(key: string, ttlMs: number, fn: () => Promise<T>): Promise<T> {
  const hit = cache.get(key);
  if (hit && hit.exp > Date.now()) return hit.val;
  let err: unknown;
  for (let i = 0; i < 3; i++) {
    try { const val = await fn(); cache.set(key, { exp: Date.now() + ttlMs, val }); return val; }
    catch (e) { err = e; await new Promise(r => setTimeout(r, 200 * 2 ** i)); }
  }
  if (hit) return hit.val; // serve stale on failure
  throw err;
}

const market = {
  meta: () => ({ provider: provider.name, demo: provider.demo, session: provider.getSessionStatus() }),
  indices: () => cached('idx', 3000, () => provider.getIndices()),
  quotes: () => cached('quotes', 3000, () => provider.getQuotes()),
  quote: (s: string) => cached('q:' + s, 3000, () => provider.getQuote(s)),
  history: (s: string, r: Range) => cached(`h:${s}:${r}`, 30000, () => provider.getHistory(s, r)),
  fundamentals: (s: string) => cached('f:' + s, 60000, () => provider.getFundamentals(s)),
};

// ===== services/newsIpo.ts =====
// DEMO placeholders, clearly labelled. Replace with a licensed news/IPO provider.
async function getNews(category?: string) {
  const demo = !env.marketKey;
  const now = new Date().toISOString();
  const items = demo ? [
    { id: 'd1', headline: 'DEMO: Sample headline about the banking sector', summary: 'Placeholder text shown only in demo mode.', publisher: 'Demo Source', publishedAt: now, url: '#', category: 'Banking' },
    { id: 'd2', headline: 'DEMO: Sample headline about technology stocks', summary: 'Placeholder text shown only in demo mode.', publisher: 'Demo Source', publishedAt: now, url: '#', category: 'Technology' },
    { id: 'd3', headline: 'DEMO: Sample headline about the Indian economy', summary: 'Placeholder text shown only in demo mode.', publisher: 'Demo Source', publishedAt: now, url: '#', category: 'Economy' },
  ] : [];
  return { demo, source: demo ? 'DEMO (not real news)' : 'configure news provider', asOf: now,
    items: category ? items.filter(i => i.category === category) : items };
}

async function getIpos() {
  const demo = !env.marketKey;
  const d = (n: number) => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10);
  return { demo, source: demo ? 'DEMO (fictional IPOs)' : 'configure IPO provider', asOf: new Date().toISOString(),
    items: demo ? [
      { company: 'Demo Upcoming Ltd (fictional)', status: 'UPCOMING', priceBand: '₹100–₹105', lotSize: 140, opens: d(5), closes: d(8), listing: d(13) },
      { company: 'Demo Open Ltd (fictional)', status: 'OPEN', priceBand: '₹250–₹260', lotSize: 57, opens: d(-1), closes: d(2), listing: d(7), subscription: '2.4x' },
      { company: 'Demo Listed Ltd (fictional)', status: 'LISTED', priceBand: '₹80–₹85', lotSize: 175, opens: d(-20), closes: d(-17), listing: d(-12), listingPrice: 98, listingGain: '+15.3%' },
    ] : [] };
}

// ===== services/gemini.ts =====
const SYSTEM = `You are an educational stock-analysis assistant for Indian markets.
RULES: Use ONLY the JSON data provided. Never invent figures. If a value is null or missing write "Data unavailable".
Do not promise returns. Do not give personalised buy/sell recommendations.
Clearly label content as FACTS (from data) vs INTERPRETATION (your reasoning). Be concise.`;

async function callGemini(prompt: string, history: { role: 'user' | 'model'; text: string }[] = []) {
  if (!env.gemini) throw new HttpError(503, 'GEMINI_API_KEY is not configured on the server');
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${env.geminiModel}:generateContent`;
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': env.gemini },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: SYSTEM }] },
      contents: [...history.map(h => ({ role: h.role, parts: [{ text: h.text }] })), { role: 'user', parts: [{ text: prompt }] }],
    }),
  });
  if (!r.ok) throw new HttpError(502, 'AI service error');
  const j: any = await r.json();
  return j.candidates?.[0]?.content?.parts?.map((p: any) => p.text).join('') || 'No response';
}

async function facts(symbol: string) {
  const [quote, fundamentals, candles] = await Promise.all([market.quote(symbol), market.fundamentals(symbol), market.history(symbol, '6M')]);
  if (!quote) throw new HttpError(404, 'Unknown symbol');
  const closes = candles.map(c => c.close);
  const sma = (n: number) => closes.length >= n ? closes.slice(-n).reduce((a, b) => a + b, 0) / n : null;
  return { dataSource: market.meta().provider, demoData: market.meta().demo, quote, fundamentals,
    technical: { sma20: sma(20), sma50: sma(50), candlesUsed: closes.length } };
}

async function analyze(symbol: string) {
  const data = await facts(symbol);
  const text = await callGemini(`Analyse this company with sections: Company Overview, Fundamental Analysis, Technical Analysis, Risk Analysis, AI Summary (positives, negatives, bullish scenario, bearish scenario, risks to monitor). DATA:\n${JSON.stringify(data)}`);
  return { symbol, generatedAt: new Date().toISOString(), data, text, disclaimer: 'Educational use only. Not investment advice.' };
}

async function chat(symbol: string, message: string, history: any[]) {
  const data = await facts(symbol);
  const text = await callGemini(`DATA:\n${JSON.stringify(data)}\n\nQUESTION: ${message}`, history);
  return { text, disclaimer: 'Educational use only. Not investment advice.' };
}

// ===== utils/portfolio.ts =====
/**
 * COST-BASIS METHODOLOGY: Weighted Average Cost.
 * - BUY: avgCost = (qty*avgCost + buyQty*price) / (qty + buyQty)
 * - SELL: realized P/L = (sellPrice - avgCost) * sellQty; avgCost unchanged; qty reduced
 * - Overselling is rejected. Brokerage/taxes and corporate actions (splits, bonus)
 *   are NOT applied automatically; record adjusted transactions manually.
 */
interface Tx { symbol: string; quantity: number; price: number; transactionType: 'BUY' | 'SELL'; transactionDate: Date | string }
interface Holding { symbol: string; quantity: number; avgCost: number; invested: number; realizedPL: number }

function computeHoldings(txs: Tx[]): Holding[] {
  const map = new Map<string, Holding>();
  const sorted = [...txs].sort((a, b) => +new Date(a.transactionDate) - +new Date(b.transactionDate));
  for (const t of sorted) {
    const h = map.get(t.symbol) ?? { symbol: t.symbol, quantity: 0, avgCost: 0, invested: 0, realizedPL: 0 };
    if (t.transactionType === 'BUY') {
      const total = h.quantity * h.avgCost + t.quantity * t.price;
      h.quantity += t.quantity;
      h.avgCost = total / h.quantity;
    } else {
      if (t.quantity > h.quantity) throw new Error(`Cannot sell ${t.quantity} ${t.symbol}; only ${h.quantity} held`);
      h.realizedPL += (t.price - h.avgCost) * t.quantity;
      h.quantity -= t.quantity;
      if (h.quantity === 0) h.avgCost = 0;
    }
    h.invested = h.quantity * h.avgCost;
    map.set(t.symbol, h);
  }
  return [...map.values()];
}

// ===== routes/auth.ts =====
const authR = Router();
const cookieOpts = { httpOnly: true, secure: env.prod, sameSite: 'lax' as 'none' | 'lax', maxAge: 7 * 864e5 };
const pub = (u: any) => ({ id: u._id, name: u.name, email: u.email, preferences: u.preferences });

const creds = z.object({ email: z.string().email(), password: z.string().min(8).max(100) });
const reg = creds.extend({ name: z.string().min(1).max(80) });

authR.post('/register', validate(reg), asyncH(async (req, res) => {
  const { name, email, password } = req.body;
  if (await User.findOne({ email })) throw new HttpError(409, 'Email already registered');
  const u = await User.create({ name, email, passwordHash: await bcrypt.hash(password, 12) });
  await VirtualAccount.create({ userId: u._id });
  res.cookie('token', signToken(String(u._id)), cookieOpts).status(201).json(pub(u));
}));

authR.post('/login', validate(creds), asyncH(async (req, res) => {
  const u = await User.findOne({ email: req.body.email });
  if (!u || !(await bcrypt.compare(req.body.password, u.passwordHash))) throw new HttpError(401, 'Invalid email or password');
  res.cookie('token', signToken(String(u._id)), cookieOpts).json(pub(u));
}));

authR.post('/logout', (_req, res) => { res.clearCookie('token', cookieOpts).json({ ok: true }); });

authR.get('/me', requireAuth, asyncH(async (_req, res) => {
  const u = await User.findById(res.locals.userId);
  if (!u) throw new HttpError(401, 'Session invalid');
  res.json(pub(u));
}));

authR.patch('/me', requireAuth, validate(z.object({ name: z.string().min(1).max(80).optional(), exchange: z.enum(['NSE', 'BSE']).optional() })), asyncH(async (req, res) => {
  const u = await User.findById(res.locals.userId);
  if (!u) throw new HttpError(401, 'Session invalid');
  if (req.body.name) u.name = req.body.name;
  if (req.body.exchange) u.set('preferences.exchange', req.body.exchange);
  await u.save();
  res.json(pub(u));
}));

authR.post('/change-password', requireAuth, validate(z.object({ current: z.string(), next: z.string().min(8).max(100) })), asyncH(async (req, res) => {
  const u = await User.findById(res.locals.userId);
  if (!u || !(await bcrypt.compare(req.body.current, u.passwordHash))) throw new HttpError(400, 'Current password incorrect');
  u.passwordHash = await bcrypt.hash(req.body.next, 12);
  await u.save();
  res.json({ ok: true });
}));

// ===== routes/market.ts =====
const mktR = Router();
const RANGES = ['1D', '1W', '1M', '3M', '6M', '1Y', '5Y'];

mktR.get('/meta', (_q, res) => res.json(market.meta()));
mktR.get('/indices', asyncH(async (_q, res) => res.json({ ...market.meta(), data: await market.indices() })));

mktR.get('/stocks', asyncH(async (req, res) => {
  let list = await market.quotes();
  const { q, sector, exchange, minCap, maxCap, sort = 'symbol', dir = 'asc' } = req.query as Record<string, string>;
  if (q) list = list.filter(s => (s.symbol + s.name).toLowerCase().includes(q.toLowerCase()));
  if (sector) list = list.filter(s => s.sector === sector);
  if (exchange) list = list.filter(s => s.exchange === exchange);
  if (minCap) list = list.filter(s => s.marketCap >= Number(minCap));
  if (maxCap) list = list.filter(s => s.marketCap <= Number(maxCap));
  const key = ['price', 'changePercent', 'volume', 'marketCap', 'symbol'].includes(sort) ? sort : 'symbol';
  list = [...list].sort((a: any, b: any) => (a[key] > b[key] ? 1 : -1) * (dir === 'desc' ? -1 : 1));
  res.json({ ...market.meta(), data: list });
}));

mktR.get('/stocks/:symbol', asyncH(async (req, res) => {
  const q = await market.quote(req.params.symbol);
  if (!q) throw new HttpError(404, 'Stock not found');
  res.json({ ...market.meta(), data: q, fundamentals: await market.fundamentals(req.params.symbol) });
}));

mktR.get('/stocks/:symbol/history', asyncH(async (req, res) => {
  const range = String(req.query.range || '1M');
  if (!RANGES.includes(range)) throw new HttpError(400, 'Invalid range');
  const data = await market.history(req.params.symbol, range as Range);
  res.json({ ...market.meta(), range, asOf: new Date().toISOString(), data });
}));

mktR.get('/gainers', asyncH(async (_q, res) => res.json({ ...market.meta(), data: [...await market.quotes()].sort((a, b) => b.changePercent - a.changePercent).slice(0, 5) })));
mktR.get('/losers', asyncH(async (_q, res) => res.json({ ...market.meta(), data: [...await market.quotes()].sort((a, b) => a.changePercent - b.changePercent).slice(0, 5) })));
mktR.get('/active', asyncH(async (_q, res) => res.json({ ...market.meta(), data: [...await market.quotes()].sort((a, b) => b.volume - a.volume).slice(0, 5) })));

mktR.get('/breadth', asyncH(async (_q, res) => {
  const q = await market.quotes();
  const sectors: Record<string, { sum: number; n: number }> = {};
  q.forEach(s => { (sectors[s.sector] ??= { sum: 0, n: 0 }); sectors[s.sector].sum += s.changePercent; sectors[s.sector].n++; });
  res.json({ ...market.meta(), asOf: new Date().toISOString(),
    advances: q.filter(s => s.change > 0).length, declines: q.filter(s => s.change < 0).length, unchanged: q.filter(s => s.change === 0).length,
    sectors: Object.entries(sectors).map(([name, v]) => ({ name, changePercent: Math.round((v.sum / v.n) * 100) / 100 })) });
}));

// ===== routes/user.ts =====
const watchlist = Router();
const sym = z.string().min(1).max(20).regex(/^[A-Za-z0-9&-]+$/).transform(s => s.toUpperCase());

watchlist.get('/', asyncH(async (_q, res) => res.json(await Watchlist.find({ userId: res.locals.userId }))));
watchlist.post('/', validate(z.object({ name: z.string().min(1).max(60).optional(), watchlistId: z.string().optional(), symbol: sym.optional() })), asyncH(async (req, res) => {
  const { name, watchlistId, symbol } = req.body;
  if (symbol && !(await market.quote(symbol))) throw new HttpError(404, 'Invalid stock');
  if (watchlistId) {
    const w = await Watchlist.findOneAndUpdate({ _id: watchlistId, userId: res.locals.userId }, symbol ? { $addToSet: { stockSymbols: symbol } } : {}, { new: true });
    if (!w) throw new HttpError(404, 'Watchlist not found');
    return res.json(w);
  }
  res.status(201).json(await Watchlist.create({ userId: res.locals.userId, name: name || 'My Watchlist', stockSymbols: symbol ? [symbol] : [] }));
}));
// DELETE /:id removes the whole list; DELETE /:id?symbol=X removes one stock
watchlist.delete('/:id', asyncH(async (req, res) => {
  const filter = { _id: req.params.id, userId: res.locals.userId };
  if (req.query.symbol) await Watchlist.updateOne(filter, { $pull: { stockSymbols: String(req.query.symbol).toUpperCase() } });
  else await Watchlist.deleteOne(filter);
  res.json({ ok: true });
}));

const portfolio = Router();
portfolio.get('/', asyncH(async (_q, res) => {
  const txs = await Transaction.find({ userId: res.locals.userId }).lean();
  const holdings = computeHoldings(txs as any);
  const quotes = await market.quotes();
  const rows = holdings.map(h => {
    const q = quotes.find(x => x.symbol === h.symbol);
    const value = q ? q.price * h.quantity : null;
    return { ...h, sector: q?.sector ?? 'Unknown', price: q?.price ?? null, value, unrealizedPL: value == null ? null : value - h.invested };
  });
  const open = rows.filter(r => r.quantity > 0);
  const invested = open.reduce((a, r) => a + r.invested, 0);
  const value = open.reduce((a, r) => a + (r.value ?? r.invested), 0);
  const realized = rows.reduce((a, r) => a + r.realizedPL, 0);
  res.json({ ...market.meta(), method: 'Weighted average cost', holdings: open, invested, value, realizedPL: realized, unrealizedPL: value - invested,
    returnPct: invested ? ((value - invested + realized) / invested) * 100 : 0, transactions: txs.slice(-50).reverse() });
}));
portfolio.get('/performance', asyncH(async (_q, res) => {
  const txs = await Transaction.find({ userId: res.locals.userId }).sort('transactionDate').lean();
  let invested = 0; const curve: { date: string; invested: number }[] = [];
  const run: any[] = [];
  for (const t of txs) {
    run.push(t);
    const hs = computeHoldings(run as any);
    invested = hs.reduce((a, h) => a + h.invested, 0);
    curve.push({ date: new Date(t.transactionDate).toISOString().slice(0, 10), invested });
  }
  res.json({ curve });
}));
portfolio.post('/transactions', validate(z.object({
  symbol: sym, quantity: z.number().int().positive().max(1e7), price: z.number().positive().max(1e7),
  transactionType: z.enum(['BUY', 'SELL']), exchange: z.enum(['NSE', 'BSE']).default('NSE'),
  transactionDate: z.coerce.date().max(new Date(Date.now() + 864e5)).optional(),
})), asyncH(async (req, res) => {
  if (!(await market.quote(req.body.symbol))) throw new HttpError(404, 'Invalid stock');
  const existing = await Transaction.find({ userId: res.locals.userId }).lean();
  try { computeHoldings([...existing, { ...req.body, transactionDate: req.body.transactionDate ?? new Date() }] as any); }
  catch (e: any) { throw new HttpError(400, e.message); }
  res.status(201).json(await Transaction.create({ ...req.body, userId: res.locals.userId }));
}));

const virtual = Router();
const START = 100000;
async function acct(userId: string) {
  return (await VirtualAccount.findOne({ userId })) ?? VirtualAccount.create({ userId });
}
virtual.get('/account', asyncH(async (_q, res) => {
  const a = await acct(res.locals.userId);
  const trades = await VirtualTrade.find({ userId: res.locals.userId }).lean();
  const holdings = computeHoldings(trades.map(t => ({ ...t, transactionType: t.tradeType, transactionDate: t.timestamp })) as any).filter(h => h.quantity > 0);
  const quotes = await market.quotes();
  const rows = holdings.map(h => { const p = quotes.find(q => q.symbol === h.symbol)?.price ?? h.avgCost; return { ...h, price: p, value: p * h.quantity, pl: (p - h.avgCost) * h.quantity }; });
  const equity = a.virtualBalance + rows.reduce((s, r) => s + r.value, 0);
  res.json({ simulated: true, balance: a.virtualBalance, holdings: rows, equity, pl: equity - START, returnPct: ((equity - START) / START) * 100 });
}));
virtual.post('/orders', validate(z.object({ symbol: sym, quantity: z.number().int().positive().max(100000), tradeType: z.enum(['BUY', 'SELL']) })), asyncH(async (req, res) => {
  const { symbol, quantity, tradeType } = req.body;
  const q = await market.quote(symbol);                       // price is ALWAYS server-side
  if (!q) throw new HttpError(404, 'Invalid stock');
  const a = await acct(res.locals.userId);
  const cost = q.price * quantity;
  const trades = await VirtualTrade.find({ userId: res.locals.userId, symbol }).lean();
  const held = computeHoldings(trades.map(t => ({ ...t, transactionType: t.tradeType, transactionDate: t.timestamp })) as any)[0]?.quantity ?? 0;
  if (tradeType === 'BUY') {
    const upd = await VirtualAccount.updateOne({ _id: a._id, virtualBalance: { $gte: cost } }, { $inc: { virtualBalance: -cost } });
    if (!upd.modifiedCount) throw new HttpError(400, 'Insufficient virtual balance');
  } else {
    if (quantity > held) throw new HttpError(400, 'Insufficient shares to sell');
    await VirtualAccount.updateOne({ _id: a._id }, { $inc: { virtualBalance: cost } });
  }
  res.status(201).json(await VirtualTrade.create({ userId: res.locals.userId, symbol, quantity, price: q.price, tradeType, simulated: true }));
}));
virtual.get('/history', asyncH(async (_q, res) => res.json(await VirtualTrade.find({ userId: res.locals.userId }).sort('-timestamp').limit(100))));
virtual.get('/leaderboard', asyncH(async (_q, res) => {
  const accts = await VirtualAccount.find().populate('userId', 'name').lean();
  const quotes = await market.quotes();
  const out = [];
  for (const a of accts) {
    const trades = await VirtualTrade.find({ userId: (a.userId as any)._id }).lean();
    const hs = computeHoldings(trades.map(t => ({ ...t, transactionType: t.tradeType, transactionDate: t.timestamp })) as any);
    const equity = a.virtualBalance + hs.reduce((s, h) => s + h.quantity * (quotes.find(q => q.symbol === h.symbol)?.price ?? h.avgCost), 0);
    out.push({ name: (a.userId as any).name, returnPct: ((equity - START) / START) * 100 });
  }
  res.json(out.sort((a, b) => b.returnPct - a.returnPct).slice(0, 20));
}));

const alerts = Router();
alerts.get('/', asyncH(async (_q, res) => res.json({ alerts: await Alert.find({ userId: res.locals.userId }).sort('-createdAt'), notifications: await Notification.find({ userId: res.locals.userId }).sort('-createdAt').limit(30) })));
alerts.post('/', validate(z.object({ symbol: sym, condition: z.enum(['PRICE_ABOVE', 'PRICE_BELOW', 'PCT_UP', 'PCT_DOWN']), targetPrice: z.number().positive() })), asyncH(async (req, res) => {
  if (!(await market.quote(req.body.symbol))) throw new HttpError(404, 'Invalid stock');
  res.status(201).json(await Alert.create({ ...req.body, userId: res.locals.userId }));
}));
alerts.delete('/:id', asyncH(async (req, res) => { await Alert.deleteOne({ _id: req.params.id, userId: res.locals.userId }); res.json({ ok: true }); }));

// ===== routes/misc.ts =====
const ai = Router();
const symbol = z.string().min(1).max(20);
ai.post('/analyze', validate(z.object({ symbol })), asyncH(async (req, res) => {
  const report = await analyze(req.body.symbol.toUpperCase());
  await AIReport.create({ userId: res.locals.userId, symbol: report.symbol, analysis: report });
  res.json(report);
}));
ai.post('/chat', validate(z.object({ symbol, message: z.string().min(1).max(1000), history: z.array(z.object({ role: z.enum(['user', 'model']), text: z.string().max(4000) })).max(20).default([]) })),
  asyncH(async (req, res) => res.json(await chat(req.body.symbol.toUpperCase(), req.body.message, req.body.history))));

const news = Router();
news.get('/', asyncH(async (req, res) => res.json(await getNews(req.query.category as string | undefined))));
const ipo = Router();
ipo.get('/', asyncH(async (_q, res) => res.json(await getIpos())));

// ===== sockets/index.ts =====
function initSockets(server: http.Server) {
  const io = new Server(server, { cors: { origin: env.client, credentials: true } });

  io.use((socket, next) => {
    const token = cookie.parse(socket.handshake.headers.cookie || '').token;
    socket.data.userId = readUserId(token); // anonymous allowed for public market data
    next();
  });
  io.on('connection', s => { if (s.data.userId) s.join('user:' + s.data.userId); });

  // broadcast market updates
  setInterval(async () => {
    if (!io.engine.clientsCount) return;
    try { io.emit('indices', { ...market.meta(), asOf: new Date().toISOString(), data: await market.indices() }); io.emit('quotes', await market.quotes()); }
    catch (e) { io.emit('market:error', 'Market data temporarily unavailable'); }
  }, 5000);

  // alert worker: each alert fires once (active=false + triggeredAt set atomically)
  setInterval(async () => {
    try {
      const active = await Alert.find({ active: true }).lean();
      if (!active.length) return;
      const quotes = await market.quotes();
      for (const a of active) {
        const q = quotes.find(x => x.symbol === a.symbol); if (!q) continue;
        const hit = (a.condition === 'PRICE_ABOVE' && q.price >= a.targetPrice) || (a.condition === 'PRICE_BELOW' && q.price <= a.targetPrice)
          || (a.condition === 'PCT_UP' && q.changePercent >= a.targetPrice) || (a.condition === 'PCT_DOWN' && q.changePercent <= -a.targetPrice);
        if (!hit) continue;
        const done = await Alert.updateOne({ _id: a._id, active: true }, { active: false, triggeredAt: new Date() });
        if (!done.modifiedCount) continue;
        const message = `${a.symbol} alert (${a.condition.replace('_', ' ').toLowerCase()} ${a.targetPrice}) triggered at ₹${q.price}${market.meta().demo ? ' [DEMO data]' : ''}`;
        await Notification.create({ userId: a.userId, message });
        io.to('user:' + a.userId).emit('alert', { message });
      }
    } catch (e) { console.error('alert worker', e); }
  }, 15000);
  return io;
}

// ===== index.ts =====
const auth = authR;
const marketRoutes = mktR;
















const app = express();
app.set('trust proxy', 1);
app.use(helmet({ contentSecurityPolicy: { directives: {
  defaultSrc: ["'self'"], scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://unpkg.com', 'https://cdn.tailwindcss.com'],
  styleSrc: ["'self'", "'unsafe-inline'"], imgSrc: ["'self'", 'data:'], connectSrc: ["'self'", 'ws:', 'wss:'] } } }));
app.use(cors({ origin: env.client, credentials: true }));
app.use(morgan(env.prod ? 'combined' : 'dev'));
app.use(express.json({ limit: '50kb' }));
app.use(cookieParser());
app.use(mongoSanitize());
app.use('/api', rateLimit({ windowMs: 60_000, limit: 200 }));
app.use('/api/auth', rateLimit({ windowMs: 15 * 60_000, limit: 50 }));
app.use('/api/ai', rateLimit({ windowMs: 60_000, limit: 10 }));
app.use('/api', csrfGuard);

app.get('/health', (_q, r) => r.json({ ok: true }));
app.use('/api/auth', auth);
app.use('/api/market', marketRoutes);
app.use('/api/news', news);
app.use('/api/ipo', ipo);
app.use('/api/watchlist', requireAuth, watchlist);
app.use('/api/portfolio', requireAuth, portfolio);
app.use('/api/virtual-trading', requireAuth, virtual);
app.use('/api/alerts', requireAuth, alerts);
app.use('/api/ai', requireAuth, ai);
app.get(/^\/(?!api|socket\.io|health).*/, (_q, res) => res.type('html').send(INDEX_HTML));
app.use(errorHandler);

const server = http.createServer(app);
initSockets(server);
mongoose.connect(env.mongo).then(() => {
  server.listen(env.port, () => console.log(`API on :${env.port}`));
}).catch(e => { console.error('Mongo connection failed', e.message); process.exit(1); });

// ===== embedded frontend (served at /) =====
const INDEX_HTML = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>StockPulse AI – Understand Markets. Invest Smarter.</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{colors:{bg:'#0B0F19',side:'#111827',card:'#151D2B',line:'#263244',brand:'#3B82F6',up:'#22C55E',down:'#EF4444',ink:'#F8FAFC',mute:'#94A3B8'}}}}</script>
<style type="text/tailwindcss">@layer components{.card{@apply bg-card border border-line rounded-xl p-4 shadow-lg shadow-black/20}.btn{@apply bg-brand hover:bg-blue-600 transition text-white rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-50}.btn-ghost{@apply border border-line hover:bg-line/40 transition rounded-lg px-3 py-2 text-sm}.input{@apply bg-bg border border-line rounded-lg px-3 py-2 text-sm outline-none focus:border-brand w-full}.skeleton{@apply animate-pulse bg-line/60 rounded}}</style>
<script src="https://unpkg.com/preact@10.22.0/dist/preact.umd.js"></script><script src="https://unpkg.com/preact@10.22.0/hooks/dist/hooks.umd.js"></script><script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script><script src="/socket.io/socket.io.js"></script></head>
<body class="bg-bg text-ink"><div id="app"></div><div id="toasts" class="fixed bottom-4 right-4 space-y-2 z-50"></div><script>const { h, render } = preact;
const { useState, useEffect, useRef, useCallback } = preactHooks;
const html = htm.bind(h);
const sock = io();
const $ = s => document.querySelector(s);
const inr = n => n == null ? 'Data unavailable' : '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });
const pct = n => n == null ? '—' : (n > 0 ? '+' : '') + n.toFixed(2) + '%';
const tone = n => (n || 0) >= 0 ? 'text-up' : 'text-down';
const when = i => i ? new Date(i).toLocaleString('en-IN') : '—';
function toast(msg, bad) { const d = document.createElement('div'); d.className = 'card ' + (bad ? 'text-down' : 'text-up'); d.textContent = msg; $('#toasts').appendChild(d); setTimeout(() => d.remove(), 6000); }
async function api(method, url, body) {
  const r = await fetch('/api' + url, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'StockPulse' }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || 'Request failed');
  return j;
}
function useApi(url, interval) {
  const [s, set] = useState({ loading: true });
  const load = useCallback(() => api('GET', url).then(d => set({ data: d }), e => set(p => p.data ? p : { error: e.message })), [url]);
  useEffect(() => { set({ loading: true }); load(); if (interval) { const t = setInterval(load, interval); return () => clearInterval(t); } }, [url, interval]);
  return { ...s, reload: load };
}
function useForm(init) { const [f, setF] = useState(init); const b = k => ({ value: f[k], onInput: e => setF({ ...f, [k]: e.target.value }) }); return [f, b, setF]; }
const act = (fn, ok, after) => async e => { if (e && e.preventDefault) e.preventDefault(); try { const r = await fn(); if (ok) toast(ok); if (after) after(r); } catch (x) { toast(x.message, 1); } };

// ---------- indicators ----------
const sma = (v, n) => v.map((_, i) => i < n - 1 ? null : v.slice(i - n + 1, i + 1).reduce((a, b) => a + b, 0) / n);
const ema = (v, n) => { const k = 2 / (n + 1), o = []; v.forEach((x, i) => o.push(i ? x * k + o[i - 1] * (1 - k) : x)); return o; };
function rsi(v, n = 14) { const out = v.map(() => null); let g = 0, l = 0; for (let i = 1; i < v.length; i++) { const d = v[i] - v[i - 1], u = Math.max(d, 0), w = Math.max(-d, 0); if (i <= n) { g += u; l += w; if (i === n) { g /= n; l /= n; out[i] = 100 - 100 / (1 + g / (l || 1e-9)); } } else { g = (g * (n - 1) + u) / n; l = (l * (n - 1) + w) / n; out[i] = 100 - 100 / (1 + g / (l || 1e-9)); } } return out; }
function macd(v) { const a = ema(v, 12), b = ema(v, 26), line = v.map((_, i) => a[i] - b[i]), signal = ema(line, 9); return { line, signal, hist: line.map((x, i) => x - signal[i]) }; }
function boll(v, n = 20) { const m = sma(v, n); return v.map((_, i) => { if (m[i] == null) return null; const s = v.slice(i - n + 1, i + 1), sd = Math.sqrt(s.reduce((a, b) => a + (b - m[i]) ** 2, 0) / n); return { up: m[i] + 2 * sd, lo: m[i] - 2 * sd }; }); }

// ---------- shared UI ----------
const Skel = ({ hh = 'h-24' }) => html\`<div class=\${'skeleton w-full ' + hh}></div>\`;
const Empty = ({ t }) => html\`<div class="text-mute text-sm py-6 text-center">\${t}</div>\`;
const Q = ({ q, render }) => q.loading ? html\`<\${Skel} hh="h-32"/>\` : q.error ? html\`<div class="text-down text-sm py-4">\${q.error}</div>\` : render(q.data);
const Page = ({ title, right, children }) => html\`<div class="space-y-4"><div class="flex items-center justify-between flex-wrap gap-2"><h1 class="text-xl font-semibold">\${title}</h1>\${right}</div>\${children}</div>\`;
const Demo = ({ d }) => !d ? null : html\`<div class=\${'text-xs ' + (d.demo ? 'text-yellow-400' : 'text-mute')}>\${d.demo ? '⚠ DEMO MODE – fictional sample data, not real market prices. ' : ''}Source: \${d.provider || d.source || '—'}\${d.asOf ? ' · as of ' + new Date(d.asOf).toLocaleTimeString('en-IN') : ''}</div>\`;
const Stat = ({ k, v, c }) => html\`<div class="card"><div class="text-mute text-xs">\${k}</div><div class=\${'font-semibold ' + (c || '')}>\${v}</div></div>\`;
const Spark = ({ d, up }) => { const mn = Math.min(...d), mx = Math.max(...d), p = d.map((v, i) => (i / (d.length - 1)) * 100 + ',' + (28 - ((v - mn) / (mx - mn || 1)) * 26)).join(' '); return html\`<svg viewBox="0 0 100 30" class="w-full h-8"><polyline fill="none" stroke-width="1.5" stroke=\${up ? '#22C55E' : '#EF4444'} points=\${p}/></svg>\`; };
const Bars = ({ items }) => { const t = items.reduce((a, b) => a + b.value, 0) || 1; return html\`<div class="space-y-1">\${items.map(i => html\`<div class="text-xs"><div class="flex justify-between"><span>\${i.label}</span><span>\${(i.value / t * 100).toFixed(1)}%</span></div><div class="h-2 bg-line rounded"><div class="h-2 bg-brand rounded" style=\${'width:' + (i.value / t * 100) + '%'}></div></div></div>\`)}</div>\`; };
const Syms = () => { const s = useApi('/market/stocks'); return html\`<datalist id="syms">\${(s.data ? s.data.data : []).map(x => html\`<option value=\${x.symbol}></option>\`)}</datalist>\`; };

// ---------- Login ----------
function Login({ onAuth }) {
  const [mode, setMode] = useState('login'); const [f, b] = useForm({ name: '', email: '', password: '' });
  return html\`<div class="min-h-screen flex items-center justify-center p-4"><form onSubmit=\${act(() => api('POST', '/auth/' + mode, f), 'Welcome to StockPulse AI', onAuth)} class="card w-full max-w-sm space-y-3">
    <div class="text-2xl font-bold">Stock<span class="text-brand">Pulse</span> AI</div><div class="text-mute text-sm">Understand Markets. Invest Smarter.</div>
    \${mode === 'register' && html\`<input class="input" placeholder="Name" required ...\${b('name')}/>\`}
    <input class="input" type="email" placeholder="Email" required ...\${b('email')}/>
    <input class="input" type="password" minlength="8" placeholder="Password (min 8 chars)" required ...\${b('password')}/>
    <button class="btn w-full">\${mode === 'login' ? 'Log in' : 'Create account'}</button>
    <button type="button" class="text-sm text-mute w-full" onClick=\${() => setMode(mode === 'login' ? 'register' : 'login')}>\${mode === 'login' ? 'New here? Register' : 'Have an account? Log in'}</button></form></div>\`;
}

// ---------- Dashboard ----------
function Dashboard() {
  const idx = useApi('/market/indices', 10000), [live, setLive] = useState(null);
  useEffect(() => { const f = p => setLive(p); sock.on('indices', f); return () => sock.off('indices', f); }, []);
  const br = useApi('/market/breadth', 10000), news = useApi('/news');
  const lists = [['Top Gainers', '/market/gainers'], ['Top Losers', '/market/losers'], ['Most Active', '/market/active']];
  const I = live || idx.data;
  return html\`<\${Page} title="Dashboard" right=\${html\`<\${Demo} d=\${I}/>\`}>
    \${I ? html\`<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">\${I.data.map(i => html\`<div class="card"><div class="text-mute text-xs">\${i.name}</div><div class="text-xl font-semibold">\${i.value.toLocaleString('en-IN')}</div>
      <div class=\${'text-sm ' + tone(i.change)}>\${i.change > 0 ? '+' : ''}\${i.change} (\${pct(i.changePercent)})</div><div class="text-mute text-xs">Prev close \${i.prevClose.toLocaleString('en-IN')}</div><\${Spark} d=\${i.spark} up=\${i.change >= 0}/></div>\`)}</div>\` : html\`<\${Skel} hh="h-36"/>\`}
    <\${Q} q=\${br} render=\${d => html\`<div class="card grid grid-cols-2 md:grid-cols-4 gap-3 text-sm"><div>Advances <b class="text-up">\${d.advances}</b></div><div>Declines <b class="text-down">\${d.declines}</b></div><div>Unchanged <b>\${d.unchanged}</b></div><div class="text-mute">Updated \${when(d.asOf)}</div></div>\`}/>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">\${lists.map(([t, u]) => { const q = useApi(u, 10000); return html\`<div class="card"><div class="font-medium mb-2">\${t}</div><\${Q} q=\${q} render=\${d => d.data.map(s => html\`<a href=\${'#/stock/' + s.symbol} class="flex justify-between py-1.5 text-sm hover:bg-line/30 rounded px-1"><span>\${s.symbol}</span><span class="flex gap-3"><span>\${inr(s.price)}</span><span class=\${'w-16 text-right ' + tone(s.changePercent)}>\${pct(s.changePercent)}</span></span></a>\`)}/></div>\`; })}</div>
    <div class="card"><div class="font-medium mb-2">Sectors</div><\${Q} q=\${br} render=\${d => html\`<div class="grid grid-cols-2 md:grid-cols-4 gap-3">\${d.sectors.map(s => html\`<a href="#/explorer" class="border border-line rounded-lg p-3 hover:bg-line/30"><div class="text-sm">\${s.name}</div><div class=\${'font-semibold ' + tone(s.changePercent)}>\${pct(s.changePercent)}</div></a>\`)}</div>\`}/></div>
    <div class="card"><div class="font-medium mb-2">Recent News</div><\${Q} q=\${news} render=\${d => d.items.length ? d.items.map(n => html\`<div class="py-1.5 text-sm"><a href="#/news" class="hover:text-brand">\${n.headline}</a><div class="text-mute text-xs">\${n.publisher} · \${when(n.publishedAt)}</div></div>\`) : html\`<\${Empty} t="No news available"/>\`}/></div><//>\`;
}

// ---------- Explorer / Markets ----------
function Explorer({ title, sort }) {
  const [f, b, setF] = useForm({ q: '', sector: '', minCap: '', sort: sort || 'symbol', dir: sort ? 'desc' : 'asc', exchange: '' });
  const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString();
  const q = useApi('/market/stocks?' + qs, 5000);
  return html\`<\${Page} title=\${title} right=\${html\`<\${Demo} d=\${q.data}/>\`}>
    <div class="card grid grid-cols-2 md:grid-cols-6 gap-2"><input class="input" placeholder="Search name/ticker" ...\${b('q')}/>
      <select class="input" ...\${b('exchange')}><option value="">NSE + BSE</option><option>NSE</option><option>BSE</option></select>
      <select class="input" ...\${b('sector')}><option value="">All sectors</option>\${['Banking', 'IT', 'Automobile', 'Pharma', 'FMCG', 'Energy', 'Metal', 'Realty'].map(s => html\`<option>\${s}</option>\`)}</select>
      <select class="input" ...\${b('minCap')}><option value="">Any market cap</option><option value="500000">Large (>₹5L Cr)</option><option value="100000">Mid+ (>₹1L Cr)</option></select>
      <select class="input" ...\${b('sort')}><option value="symbol">Sort: Symbol</option><option value="price">Price</option><option value="changePercent">% Change</option><option value="volume">Volume</option></select>
      <select class="input" ...\${b('dir')}><option value="asc">Ascending</option><option value="desc">Descending</option></select></div>
    <div class="card overflow-x-auto"><\${Q} q=\${q} render=\${d => !d.data.length ? html\`<\${Empty} t="No stocks match your filters"/>\` : html\`<table class="w-full text-sm"><thead class="text-mute text-left"><tr><th>Symbol</th><th>Company</th><th>Sector</th><th class="text-right">Price</th><th class="text-right">Change</th><th class="text-right">Volume</th></tr></thead><tbody>\${d.data.map(s => html\`<tr class="border-t border-line hover:bg-line/30"><td class="py-2"><a class="text-brand" href=\${'#/stock/' + s.symbol}>\${s.symbol}</a></td><td>\${s.name}</td><td>\${s.sector}</td><td class="text-right">\${inr(s.price)}</td><td class=\${'text-right ' + tone(s.changePercent)}>\${pct(s.changePercent)}</td><td class="text-right">\${s.volume.toLocaleString('en-IN')}</td></tr>\`)}</tbody></table>\`}/></div><//>\`;
}

// ---------- Stock detail ----------
function Charts({ candles }) {
  const m = useRef(), r = useRef(), c3 = useRef();
  useEffect(() => {
    if (!candles.length) return;
    const L = LightweightCharts, cl = candles.map(c => c.close), t = candles.map(c => c.time), w = m.current.clientWidth;
    const base = ht => ({ height: ht, width: w, layout: { background: { color: '#151D2B' }, textColor: '#94A3B8' }, grid: { vertLines: { color: '#263244' }, horzLines: { color: '#263244' } }, timeScale: { timeVisible: true } });
    const ln = v => v.map((x, i) => x == null ? null : { time: t[i], value: x }).filter(Boolean);
    const a = L.createChart(m.current, base(340)), b = L.createChart(r.current, base(120)), c = L.createChart(c3.current, base(140));
    a.addCandlestickSeries({ upColor: '#22C55E', downColor: '#EF4444', borderVisible: false, wickUpColor: '#22C55E', wickDownColor: '#EF4444' }).setData(candles);
    const vol = a.addHistogramSeries({ priceScaleId: 'vol', color: '#3B82F655' }); a.priceScale('vol').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } }); vol.setData(candles.map(x => ({ time: x.time, value: x.volume })));
    a.addLineSeries({ color: '#F59E0B', lineWidth: 1 }).setData(ln(sma(cl, 20))); a.addLineSeries({ color: '#A78BFA', lineWidth: 1 }).setData(ln(sma(cl, 50)));
    const bb = boll(cl); a.addLineSeries({ color: '#64748B', lineWidth: 1, lineStyle: 2 }).setData(ln(bb.map(x => x && x.up))); a.addLineSeries({ color: '#64748B', lineWidth: 1, lineStyle: 2 }).setData(ln(bb.map(x => x && x.lo)));
    b.addLineSeries({ color: '#3B82F6', lineWidth: 1 }).setData(ln(rsi(cl)));
    const md = macd(cl); c.addHistogramSeries({}).setData(md.hist.map((v, i) => ({ time: t[i], value: v, color: v >= 0 ? '#22C55E' : '#EF4444' }))); c.addLineSeries({ color: '#3B82F6', lineWidth: 1 }).setData(ln(md.line)); c.addLineSeries({ color: '#F59E0B', lineWidth: 1 }).setData(ln(md.signal));
    [a, b, c].forEach(x => x.timeScale().fitContent());
    return () => [a, b, c].forEach(x => x.remove());
  }, [candles]);
  return html\`<div class="space-y-1"><div class="text-xs text-mute">Candles + Volume · SMA20 (amber) · SMA50 (purple) · Bollinger Bands (dashed)</div><div ref=\${m}></div><div class="text-xs text-mute">RSI (14)</div><div ref=\${r}></div><div class="text-xs text-mute">MACD (12,26,9)</div><div ref=\${c3}></div></div>\`;
}
function StockDetail({ symbol }) {
  const [range, setRange] = useState('3M'), q = useApi('/market/stocks/' + symbol, 5000), hq = useApi('/market/stocks/' + symbol + '/history?range=' + range);
  const row = (k, v) => html\`<div class="flex justify-between py-1 text-sm border-b border-line/50"><span class="text-mute">\${k}</span><span>\${v == null ? 'Data unavailable' : v}</span></div>\`;
  return html\`<\${Q} q=\${q} render=\${d => { const s = d.data, f = d.fundamentals || {}; return html\`<\${Page} title=\${s.name + ' (' + s.symbol + ')'} right=\${html\`<\${Demo} d=\${{ ...d, asOf: s.asOf }}/>\`}>
    <div class="card flex flex-wrap items-end gap-6"><div><div class="text-3xl font-semibold">\${inr(s.price)}</div><div class=\${tone(s.changePercent)}>\${s.change > 0 ? '+' : ''}\${s.change} (\${pct(s.changePercent)})</div></div><div class="text-xs text-mute">\${s.exchange} · \${s.sector}</div></div>
    <div class="card"><div class="flex gap-1 mb-2 flex-wrap">\${['1D', '1W', '1M', '3M', '6M', '1Y', '5Y'].map(x => html\`<button class=\${x === range ? 'btn' : 'btn-ghost'} onClick=\${() => setRange(x)}>\${x}</button>\`)}</div>
      <div class="text-xs text-mute mb-2">Timeframe: \${range} · Data as of \${when(hq.data && hq.data.asOf)}</div><\${Q} q=\${hq} render=\${h2 => html\`<\${Charts} candles=\${h2.data}/>\`}/></div>
    <div class="grid md:grid-cols-2 gap-4"><div class="card"><div class="font-medium mb-1">Market data</div>\${row('Day high / low', inr(s.high) + ' / ' + inr(s.low))}\${row('52-week high / low', inr(s.week52High) + ' / ' + inr(s.week52Low))}\${row('Previous close', inr(s.prevClose))}\${row('Volume', s.volume.toLocaleString('en-IN'))}\${row('Market cap (₹ Cr)', s.marketCap.toLocaleString('en-IN'))}</div>
      <div class="card"><div class="font-medium mb-1">Fundamentals</div>\${[['P/E', 'pe'], ['P/B', 'pb'], ['EPS', 'eps'], ['ROE %', 'roe'], ['ROCE %', 'roce'], ['Debt/Equity', 'debtToEquity'], ['Revenue growth %', 'revenueGrowth'], ['Profit growth %', 'profitGrowth'], ['Dividend yield %', 'dividendYield']].map(([k, key]) => row(k, f[key]))}</div></div><//>\`; }}/>\`;
}

// ---------- Watchlist ----------
function Watchlist() {
  const q = useApi('/watchlist'), st = useApi('/market/stocks', 5000), [name, setName] = useState(''), [sym, setSym] = useState({});
  const px = s => st.data && st.data.data.find(x => x.symbol === s);
  return html\`<\${Page} title="Watchlists"><\${Syms}/>
    <form class="card flex gap-2" onSubmit=\${act(() => api('POST', '/watchlist', { name }), null, () => { setName(''); q.reload(); })}><input class="input" placeholder="New watchlist name" required value=\${name} onInput=\${e => setName(e.target.value)}/><button class="btn">Create</button></form>
    <\${Q} q=\${q} render=\${d => !d.length ? html\`<\${Empty} t="No watchlists yet. Create one above."/>\` : d.map(w => html\`<div class="card"><div class="flex justify-between mb-2"><b>\${w.name}</b><button class="text-down text-xs" onClick=\${act(() => api('DELETE', '/watchlist/' + w._id), null, q.reload)}>Delete list</button></div>
      <form class="flex gap-2 mb-2" onSubmit=\${act(() => api('POST', '/watchlist', { watchlistId: w._id, symbol: sym[w._id] }), null, () => { setSym({ ...sym, [w._id]: '' }); q.reload(); })}><input list="syms" class="input" placeholder="Add symbol" required value=\${sym[w._id] || ''} onInput=\${e => setSym({ ...sym, [w._id]: e.target.value })}/><button class="btn">Add</button></form>
      \${!w.stockSymbols.length ? html\`<\${Empty} t="Empty list"/>\` : w.stockSymbols.map(s => { const p = px(s); return html\`<div class="flex items-center justify-between py-1.5 text-sm border-t border-line"><a href=\${'#/stock/' + s} class="text-brand w-32">\${s}</a><span>\${p ? inr(p.price) : '—'}</span><span class=\${tone(p && p.changePercent)}>\${p ? pct(p.changePercent) : '—'}</span><span class="text-mute text-xs hidden md:block">\${p ? when(p.asOf) : ''}</span><button onClick=\${act(() => api('DELETE', '/watchlist/' + w._id + '?symbol=' + s), null, q.reload)}>✕</button></div>\`; })}</div>\`)}/><//>\`;
}

// ---------- Portfolio ----------
function Portfolio() {
  const q = useApi('/portfolio', 10000), pf = useApi('/portfolio/performance'), [f, b, setF] = useForm({ symbol: '', quantity: '', price: '', transactionType: 'BUY', exchange: 'NSE' });
  return html\`<\${Page} title="My Portfolio" right=\${html\`<\${Demo} d=\${q.data}/>\`}><\${Syms}/>
    <form class="card grid grid-cols-2 md:grid-cols-6 gap-2" onSubmit=\${act(() => api('POST', '/portfolio/transactions', { ...f, symbol: f.symbol.toUpperCase(), quantity: +f.quantity, price: +f.price }), 'Transaction recorded', () => { setF({ ...f, symbol: '', quantity: '', price: '' }); q.reload(); pf.reload(); })}>
      <input list="syms" class="input" placeholder="Symbol" required ...\${b('symbol')}/><input class="input" type="number" min="1" placeholder="Qty" required ...\${b('quantity')}/><input class="input" type="number" step="0.01" min="0.01" placeholder="Price" required ...\${b('price')}/>
      <select class="input" ...\${b('transactionType')}><option>BUY</option><option>SELL</option></select><select class="input" ...\${b('exchange')}><option>NSE</option><option>BSE</option></select><button class="btn">Add</button></form>
    <\${Q} q=\${q} render=\${d => html\`<div class="grid grid-cols-2 md:grid-cols-5 gap-3"><\${Stat} k="Invested" v=\${inr(d.invested)}/><\${Stat} k="Current value" v=\${inr(d.value)}/><\${Stat} k="Realized P/L" v=\${inr(d.realizedPL)} c=\${tone(d.realizedPL)}/><\${Stat} k="Unrealized P/L" v=\${inr(d.unrealizedPL)} c=\${tone(d.unrealizedPL)}/><\${Stat} k="Overall return" v=\${pct(d.returnPct)} c=\${tone(d.returnPct)}/></div>
      <div class="text-xs text-mute">Cost basis: \${d.method}. Brokerage, taxes and corporate actions are not auto-applied.</div>
      \${!d.holdings.length ? html\`<\${Empty} t="No holdings yet. Add your first transaction above."/>\` : html\`<div class="card overflow-x-auto"><table class="w-full text-sm"><thead class="text-mute text-left"><tr><th>Stock</th><th>Qty</th><th>Avg cost</th><th>LTP</th><th>Unrealized P/L</th></tr></thead><tbody>\${d.holdings.map(x => html\`<tr class="border-t border-line"><td class="py-2">\${x.symbol}</td><td>\${x.quantity}</td><td>\${inr(x.avgCost)}</td><td>\${inr(x.price)}</td><td class=\${tone(x.unrealizedPL)}>\${inr(x.unrealizedPL)}</td></tr>\`)}</tbody></table></div>
      <div class="grid md:grid-cols-4 gap-4"><div class="card"><div class="font-medium mb-2">Investment allocation</div><\${Bars} items=\${d.holdings.map(x => ({ label: x.symbol, value: x.invested }))}/></div>
        <div class="card"><div class="font-medium mb-2">Sector allocation</div><\${Bars} items=\${Object.entries(d.holdings.reduce((a, x) => (a[x.sector] = (a[x.sector] || 0) + (x.value == null ? x.invested : x.value), a), {})).map(([label, value]) => ({ label, value }))}/></div>
        <div class="card"><div class="font-medium mb-2">P/L distribution</div>\${d.holdings.map(x => html\`<div class="flex justify-between text-sm"><span>\${x.symbol}</span><span class=\${tone(x.unrealizedPL)}>\${inr(x.unrealizedPL)}</span></div>\`)}</div>
        <div class="card"><div class="font-medium mb-2">Invested over time</div><\${Q} q=\${pf} render=\${p => p.curve.length > 1 ? html\`<\${Spark} d=\${p.curve.map(c => c.invested)} up=\${true}/>\` : html\`<\${Empty} t="Need 2+ transactions"/>\`}/></div></div>\`}\`}/><//>\`;
}

// ---------- AI Analyst ----------
function AIAnalyst() {
  const [symbol, setSymbol] = useState('DEMOBANK'), [rep, setRep] = useState(null), [msgs, setMsgs] = useState([]), [input, setInput] = useState(''), [busy, setBusy] = useState(false);
  const run = async () => { setBusy(true); try { setRep(await api('POST', '/ai/analyze', { symbol })); setMsgs([]); } catch (x) { toast(x.message, 1); } setBusy(false); };
  const send = async e => { e.preventDefault(); const m = input; setInput(''); try { const r = await api('POST', '/ai/chat', { symbol: rep.symbol, message: m, history: msgs }); setMsgs([...msgs, { role: 'user', text: m }, { role: 'model', text: r.text }]); } catch (x) { toast(x.message, 1); } };
  return html\`<\${Page} title="AI Stock Analyst"><\${Syms}/>
    <div class="card flex gap-2"><input list="syms" class="input" value=\${symbol} onInput=\${e => setSymbol(e.target.value.toUpperCase())}/><button class="btn whitespace-nowrap" disabled=\${busy} onClick=\${run}>\${busy ? 'Analysing…' : 'Analyse'}</button></div>
    \${rep && html\`<div class="card text-xs"><b>Verified data (FACTS)</b> – source: \${rep.data.dataSource}\${rep.data.demoData ? ' (DEMO fictional data)' : ''} · as of \${when(rep.data.quote.asOf)}<pre class="mt-2 overflow-auto text-mute">\${JSON.stringify({ quote: rep.data.quote, fundamentals: rep.data.fundamentals, technical: rep.data.technical }, null, 2)}</pre></div>
      <div class="card"><div class="text-xs text-brand mb-2">AI-GENERATED INTERPRETATION · \${when(rep.generatedAt)}</div><div class="whitespace-pre-wrap text-sm">\${rep.text}</div></div>
      <div class="card"><div class="font-medium mb-2">Ask about \${rep.symbol}</div><div class="space-y-2 max-h-80 overflow-auto mb-2">\${msgs.map(m => html\`<div class=\${'text-sm p-2 rounded whitespace-pre-wrap ' + (m.role === 'user' ? 'bg-brand/15' : 'bg-line/40')}>\${m.text}</div>\`)}</div>
      <form class="flex gap-2" onSubmit=\${send}><input class="input" required placeholder="e.g. What are the main risks?" value=\${input} onInput=\${e => setInput(e.target.value)}/><button class="btn">Send</button></form></div>\`}
    <div class="text-xs text-mute">Educational use only. Not investment advice. AI can make mistakes; verify with official filings.</div><//>\`;
}

// ---------- Virtual trading ----------
function Virtual() {
  const ac = useApi('/virtual-trading/account', 10000), hi = useApi('/virtual-trading/history'), bd = useApi('/virtual-trading/leaderboard'), st = useApi('/market/stocks', 5000), [f, b, setF] = useForm({ symbol: '', quantity: '1', tradeType: 'BUY' });
  const p = st.data && st.data.data.find(x => x.symbol === f.symbol.toUpperCase());
  const all = () => { ac.reload(); hi.reload(); bd.reload(); };
  return html\`<\${Page} title="Virtual Trading (Simulated)"><\${Syms}/><div class="text-xs text-yellow-400">Paper trading only. No real money, no brokerage connection. Every transaction is simulated.</div>
    <\${Q} q=\${ac} render=\${d => html\`<div class="grid grid-cols-2 md:grid-cols-4 gap-3"><\${Stat} k="Virtual balance" v=\${inr(d.balance)}/><\${Stat} k="Total equity" v=\${inr(d.equity)}/><\${Stat} k="P/L" v=\${inr(d.pl)} c=\${tone(d.pl)}/><\${Stat} k="Return" v=\${pct(d.returnPct)} c=\${tone(d.returnPct)}/></div>\`}/>
    <form class="card grid grid-cols-2 md:grid-cols-5 gap-2 items-center" onSubmit=\${act(() => api('POST', '/virtual-trading/orders', { symbol: f.symbol.toUpperCase(), quantity: +f.quantity, tradeType: f.tradeType }), 'Simulated order executed', all)}>
      <input list="syms" class="input" placeholder="Symbol" required ...\${b('symbol')}/><input class="input" type="number" min="1" ...\${b('quantity')}/><select class="input" ...\${b('tradeType')}><option>BUY</option><option>SELL</option></select>
      <div class="text-sm text-mute">Est. value: \${p ? inr(p.price * (+f.quantity || 0)) : '—'}</div><button class="btn">Confirm simulated \${f.tradeType.toLowerCase()}</button></form>
    <div class="grid md:grid-cols-2 gap-4"><div class="card"><div class="font-medium mb-2">Holdings</div><\${Q} q=\${ac} render=\${d => !d.holdings.length ? html\`<\${Empty} t="No holdings"/>\` : d.holdings.map(x => html\`<div class="flex justify-between text-sm py-1"><span>\${x.symbol} × \${x.quantity}</span><span class=\${tone(x.pl)}>\${inr(x.pl)}</span></div>\`)}/></div>
      <div class="card"><div class="font-medium mb-2">Leaderboard</div><\${Q} q=\${bd} render=\${d => !d.length ? html\`<\${Empty} t="No traders yet"/>\` : d.map((x, i) => html\`<div class="flex justify-between text-sm py-1"><span>\${i + 1}. \${x.name}</span><span class=\${tone(x.returnPct)}>\${pct(x.returnPct)}</span></div>\`)}/></div></div>
    <div class="card"><div class="font-medium mb-2">Transaction history</div><\${Q} q=\${hi} render=\${d => !d.length ? html\`<\${Empty} t="No trades yet"/>\` : d.map(t => html\`<div class="flex justify-between text-sm py-1 border-t border-line"><span>\${t.tradeType} \${t.quantity} \${t.symbol} @ \${inr(t.price)} <i class="text-yellow-400">[SIMULATED]</i></span><span class="text-mute">\${when(t.timestamp)}</span></div>\`)}/></div><//>\`;
}

// ---------- News / IPO ----------
function News() {
  const [c, setC] = useState(''), q = useApi('/news?category=' + encodeURIComponent(c));
  return html\`<\${Page} title="Market News" right=\${html\`<\${Demo} d=\${q.data}/>\`}><div class="flex gap-2 flex-wrap">\${['', 'Indian stock market', 'Company news', 'Banking', 'Technology', 'Economy', 'IPO', 'Global markets'].map(x => html\`<button class=\${x === c ? 'btn' : 'btn-ghost'} onClick=\${() => setC(x)}>\${x || 'All'}</button>\`)}</div>
    <\${Q} q=\${q} render=\${d => !d.items.length ? html\`<\${Empty} t="No news available for this category"/>\` : d.items.map(n => html\`<div class="card"><div class="font-medium">\${n.headline}</div><p class="text-sm text-mute my-1">\${n.summary}</p><div class="text-xs text-mute">\${n.publisher} · \${when(n.publishedAt)} · <a class="text-brand" href=\${n.url} target="_blank" rel="noreferrer">Original article</a></div></div>\`)}/>
    <div class="text-xs text-mute">Add a licensed news provider in getNews() to enable real headlines; AI summaries can then use the Gemini service.</div><//>\`;
}
function IPO() {
  const q = useApi('/ipo');
  return html\`<\${Page} title="IPO Center" right=\${html\`<\${Demo} d=\${q.data}/>\`}><\${Q} q=\${q} render=\${d => !d.items.length ? html\`<\${Empty} t="No IPO data available"/>\` : ['OPEN', 'UPCOMING', 'LISTED', 'CLOSED'].map(s => { const r = d.items.filter(i => i.status === s); return r.length ? html\`<div class="card"><div class="font-medium mb-2">\${s[0] + s.slice(1).toLowerCase()}</div>\${r.map(i => html\`<div class="grid grid-cols-2 md:grid-cols-6 gap-2 text-sm py-2 border-t border-line"><b>\${i.company}</b><span>\${i.priceBand}</span><span>Lot \${i.lotSize}</span><span>\${i.opens} → \${i.closes}</span><span>List \${i.listing}</span><span>\${i.subscription ? 'Subscribed ' + i.subscription : i.listingGain ? 'Listed ₹' + i.listingPrice + ' (' + i.listingGain + ')' : '—'}</span></div>\`)}</div>\` : null; })}/><//>\`;
}

// ---------- Alerts / Settings ----------
function Alerts() {
  const q = useApi('/alerts', 8000), [f, b, setF] = useForm({ symbol: '', condition: 'PRICE_ABOVE', targetPrice: '' });
  useEffect(() => { const x = () => q.reload(); sock.on('alert', x); return () => sock.off('alert', x); }, [q.reload]);
  return html\`<\${Page} title="Alerts"><\${Syms}/>
    <form class="card grid grid-cols-2 md:grid-cols-4 gap-2" onSubmit=\${act(() => api('POST', '/alerts', { ...f, symbol: f.symbol.toUpperCase(), targetPrice: +f.targetPrice }), 'Alert created', q.reload)}><input list="syms" class="input" placeholder="Symbol" required ...\${b('symbol')}/>
      <select class="input" ...\${b('condition')}><option value="PRICE_ABOVE">Price above</option><option value="PRICE_BELOW">Price below</option><option value="PCT_UP">% increase (day)</option><option value="PCT_DOWN">% decrease (day)</option></select>
      <input class="input" type="number" step="0.01" placeholder="Target (₹ or %)" required ...\${b('targetPrice')}/><button class="btn">Create alert</button></form>
    <\${Q} q=\${q} render=\${d => html\`<div class="card"><div class="font-medium mb-2">Your alerts</div>\${!d.alerts.length ? html\`<\${Empty} t="No alerts"/>\` : d.alerts.map(a => html\`<div class="flex justify-between text-sm py-1.5 border-t border-line"><span>\${a.symbol} · \${a.condition.replace('_', ' ').toLowerCase()} \${a.targetPrice}</span><span class="flex gap-3"><span class=\${a.active ? 'text-up' : 'text-mute'}>\${a.active ? 'Active' : 'Triggered'}</span><button class="text-down" onClick=\${act(() => api('DELETE', '/alerts/' + a._id), null, q.reload)}>Delete</button></span></div>\`)}</div>
      <div class="card"><div class="font-medium mb-2">Notifications</div>\${!d.notifications.length ? html\`<\${Empty} t="No notifications yet"/>\` : d.notifications.map(n => html\`<div class="text-sm py-1.5 border-t border-line">\${n.message} <span class="text-mute text-xs">\${when(n.createdAt)}</span></div>\`)}</div>\`}/><//>\`;
}
function Settings({ user, onAuth }) {
  const [name, setName] = useState(user.name), [pw, pb, setPw] = useForm({ current: '', next: '' });
  return html\`<\${Page} title="Settings"><form class="card space-y-2 max-w-md" onSubmit=\${act(() => api('PATCH', '/auth/me', { name }), 'Profile updated', onAuth)}><div class="font-medium">Profile</div><div class="text-sm text-mute">\${user.email}</div><input class="input" value=\${name} onInput=\${e => setName(e.target.value)}/><button class="btn">Save</button></form>
    <form class="card space-y-2 max-w-md" onSubmit=\${act(() => api('POST', '/auth/change-password', pw), 'Password changed', () => setPw({ current: '', next: '' }))}><div class="font-medium">Change password</div><input class="input" type="password" placeholder="Current" required ...\${pb('current')}/><input class="input" type="password" minlength="8" placeholder="New (min 8)" required ...\${pb('next')}/><button class="btn">Update</button></form><//>\`;
}

// ---------- Shell + App ----------
const NAV = [['/', 'Dashboard'], ['/markets', 'Markets'], ['/explorer', 'Stock Explorer'], ['/watchlist', 'Watchlist'], ['/portfolio', 'My Portfolio'], ['/ai', 'AI Stock Analyst'], ['/virtual', 'Virtual Trading'], ['/news', 'Market News'], ['/ipo', 'IPO Center'], ['/alerts', 'Alerts'], ['/settings', 'Settings']];
function useHash() { const [p, setP] = useState(location.hash.slice(1) || '/'); useEffect(() => { const f = () => { setP(location.hash.slice(1) || '/'); }; addEventListener('hashchange', f); return () => removeEventListener('hashchange', f); }, []); return p; }
function Shell({ user, setUser }) {
  const route = useHash(), [open, setOpen] = useState(false), [on, setOn] = useState(sock.connected), [q, setQ] = useState(''), [hits, setHits] = useState([]), [ex, setEx] = useState('NSE'), meta = useApi('/market/meta', 30000);
  useEffect(() => { const c = () => setOn(true), d = () => setOn(false), a = p => toast(p.message); sock.on('connect', c); sock.on('disconnect', d); sock.on('alert', a); return () => { sock.off('connect', c); sock.off('disconnect', d); sock.off('alert', a); }; }, []);
  useEffect(() => { if (q.length < 2) return setHits([]); api('GET', '/market/stocks?q=' + encodeURIComponent(q)).then(r => setHits(r.data), () => setHits([])); }, [q]);
  const m = meta.data, sm = route.match(/^\\/stock\\/(.+)$/);
  const page = sm ? html\`<\${StockDetail} key=\${sm[1]} symbol=\${sm[1]}/>\` : route === '/markets' ? html\`<\${Explorer} title="Markets" sort="changePercent"/>\` : route === '/explorer' ? html\`<\${Explorer} title="Stock Explorer"/>\` : route === '/watchlist' ? html\`<\${Watchlist}/>\` : route === '/portfolio' ? html\`<\${Portfolio}/>\` : route === '/ai' ? html\`<\${AIAnalyst}/>\` : route === '/virtual' ? html\`<\${Virtual}/>\` : route === '/news' ? html\`<\${News}/>\` : route === '/ipo' ? html\`<\${IPO}/>\` : route === '/alerts' ? html\`<\${Alerts}/>\` : route === '/settings' ? html\`<\${Settings} user=\${user} onAuth=\${setUser}/>\` : html\`<\${Dashboard}/>\`;
  return html\`<div class="min-h-screen flex"><aside class=\${'fixed md:static z-30 inset-y-0 left-0 w-56 bg-side border-r border-line p-3 transition-transform ' + (open ? '' : '-translate-x-full md:translate-x-0')}><div class="font-bold text-lg px-2 py-3">Stock<span class="text-brand">Pulse</span> AI</div>
    <nav class="space-y-1">\${NAV.map(([to, l]) => html\`<a href=\${'#' + to} onClick=\${() => setOpen(false)} class=\${'block px-3 py-2 rounded-lg text-sm transition ' + (route === to ? 'bg-brand/15 text-brand' : 'text-mute hover:bg-line/40')}>\${l}</a>\`)}</nav></aside>
    <div class="flex-1 min-w-0"><header class="sticky top-0 z-20 bg-bg/90 backdrop-blur border-b border-line px-4 py-3 flex items-center gap-3"><button class="md:hidden" onClick=\${() => setOpen(!open)}>☰</button>
      <div class="relative flex-1 max-w-md"><input class="input" placeholder="Search company or symbol" value=\${q} onInput=\${e => setQ(e.target.value)}/>\${q.length > 1 && html\`<div class="absolute mt-1 w-full card p-1 max-h-64 overflow-auto">\${hits.length ? hits.map(s => html\`<a href=\${'#/stock/' + s.symbol} onClick=\${() => setQ('')} class="block px-3 py-2 text-sm hover:bg-line/40 rounded"><b>\${s.symbol}</b> <span class="text-mute">\${s.name}</span></a>\`) : html\`<div class="text-mute text-sm p-3">No matches</div>\`}</div>\`}</div>
      <select class="input w-20" value=\${ex} onInput=\${e => setEx(e.target.value)}><option>NSE</option><option>BSE</option></select>
      <span class=\${'text-xs px-2 py-1 rounded-full ' + (m && m.session.open ? 'bg-up/15 text-up' : 'bg-down/15 text-down')}>\${m ? m.session.label : '…'}</span>
      <span title=\${on ? 'Live connection' : 'Disconnected – data may be stale'} class=\${on ? 'text-up' : 'text-down'}>●</span><a href="#/alerts" title="Alerts">🔔</a><span class="text-sm hidden sm:block">\${user.name}</span>
      <button class="text-mute text-sm" onClick=\${act(() => api('POST', '/auth/logout'), null, () => setUser(null))}>Logout</button></header>
    \${m && m.demo && html\`<div class="bg-yellow-500/10 text-yellow-300 text-xs px-4 py-2">DEMO MODE: all prices, news and IPOs are fictional sample data. Set MARKET_PROVIDER_KEY and implement a licensed provider in LiveProvider for real data.</div>\`}
    <main class="p-4 md:p-6">\${page}</main></div></div>\`;
}
function App() {
  const [user, setUser] = useState(undefined);
  useEffect(() => { api('GET', '/auth/me').then(setUser, () => setUser(null)); }, []);
  if (user === undefined) return html\`<div class="p-10 text-mute">Loading…</div>\`;
  return user ? html\`<\${Shell} user=\${user} setUser=\${setUser}/>\` : html\`<\${Login} onAuth=\${setUser}/>\`;
}
render(html\`<\${App}/>\`, $('#app'));
</script></body></html>`;

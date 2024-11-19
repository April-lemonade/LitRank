//backend
import * as d3 from "d3";

export const BASE_URL = 'http://localhost:8000';

export const borderStyle = 'solid #D9D9D9 1px'

// parameter view
export const BARCHART_MARGIN_HORIZONTAL = 28;
export const BARCHART_MARGIN_VERTICAL = 60;

export const COLORS = [
    ['bg-stone-100', 'bg-stone-200', 'bg-stone-300', 'bg-stone-400', 'bg-stone-500'],
    ['bg-slate-100', 'bg-slate-200', 'bg-slate-300', 'bg-slate-400', 'bg-slate-500'],
    ['bg-gray-100', 'bg-gray-200', 'bg-gray-300', 'bg-gray-400', 'bg-gray-500'],
    ['bg-zinc-100', 'bg-zinc-200', 'bg-zinc-300', 'bg-zinc-400', 'bg-zinc-500'],
    ['bg-neutral-100', 'bg-neutral-200', 'bg-neutral-300', 'bg-neutral-400', 'bg-neutral-500']
]

export const roles = [
    "像贊作者", "校註者", "輓詞作者", "題辭", "序作者", "年譜作者", "傳記作者", "跋作者",
    "作者", "校閲", "None", "其他作者", "附記作者", "凡例作者", "墓志詺作者", "编輯", "主要作者"
];

export const roleColor = d3.scaleOrdinal()
    .domain(roles)
    .range(d3.schemeTableau10.concat(d3.schemeSet3));


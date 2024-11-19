<script>
    import {onMount} from "svelte";
    import {BARCHART_MARGIN_HORIZONTAL, BARCHART_MARGIN_VERTICAL} from "../constants.js";
    import * as d3 from "d3";

    export let width;
    export let height;
    export let BASE_URL;
    export let workColStats;

    let xScale, yScale;

    let data = [];
    let tooltipVisible = false;
    let tooltipContent = "";
    let tooltipX = 0;
    let tooltipY = 0;

    $: if (workColStats.length > 0) {
        data = workColStats
        const entries = Object.entries(data[0]);
        const svg = d3.select(".columnStat");
        xScale = d3.scaleLinear()
            .domain([0, d3.max(entries, d => d[1])])
            .range([0, width]);

        yScale = d3.scaleBand()
            .domain(entries.map(d => d[0]))
            .range([0, height])
            .padding(0.1);
        // xScale = d3.scaleBand()
        //     .domain(entries.map(d => d[0]))
        //     .range([BARCHART_MARGIN_HORIZONTAL, width - BARCHART_MARGIN_HORIZONTAL])
        //     .padding(0.1);
        // yScale = d3.scaleLinear()
        //     .domain([0, d3.max(entries, d => d[1])])
        //     .range([height - BARCHART_MARGIN_VERTICAL, 0]);

        svg.selectAll(".x-axis")
            .data([null])
            .join("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0, ${height - BARCHART_MARGIN_VERTICAL})`)
        // .call(d3.axisBottom(xScale));

        svg
            .selectAll(".y-axis")
            .data([null])
            .join("g")
            .attr("class", "y-axis")
            .attr("transform", `translate(${BARCHART_MARGIN_HORIZONTAL}, 0)`)
        // .call(d3.axisLeft(yScale).ticks(4));

        const tooltip = svg.append("text")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .attr("background-color", "black")
            .attr("color", "white")
            .attr("padding", "5px")
            .attr("border-radius", "4px");

        svg.selectAll("rect")
            .data(entries)
            .join("rect")
            .attr("y", d => yScale(d[0]))
            .attr("height", yScale.bandwidth())
            .attr("x", 0)
            .attr("width", d => xScale(d[1]))
            .attr("fill", "steelblue")
            .on("mouseover", function (event, d) {
                tooltip
                    .style("opacity", 1)
                    .text(`${d[0]}: ${d[1]}`)
                    .attr("x", event.x + 20)
                    .attr("y", event.y - 10);
            })
            .on("mouseout", () => tooltip.style("opacity", 0));
    }

    function showTooltip(event, d) {
        console.log(event)
        // tooltipContent = `${d[0]}: ${d[1]}`;
        // tooltipX = event.layerX + 10; // Offset tooltip position
        // tooltipY = event.layerY;
        // tooltipVisible = true;
    }

    function hideTooltip() {
        // tooltipVisible = false;
    }
</script>

<div bind:clientWidth={width} bind:clientHeight={height} style="height: {height};width:{width}">
    <svg width="100%" height="100%" class="columnStat">
        {#each Object.entries(data[0] || {}) as [key, value]}
            <rect y={yScale(key)}
                  height={yScale.bandwidth()}
                  x="0"
                  width={xScale(value)}
                  fill="steelblue"
                  on:mouseover={event => showTooltip(event, [key, value])}
                  on:mouseout={hideTooltip}></rect>
        {/each}
        {#if tooltipVisible}
            <text x={tooltipX} y={tooltipY} fill="black" class="tooltip-text bg-black text-sm">
                {@html tooltipContent}
            </text>
        {/if}
    </svg>
</div>

<style>
    .tooltip {
        font-size: 12px;
        pointer-events: none;
        background-color: black;
        padding: 5px;
        border-radius: 4px;
        fill: white; /* SVG text fill color for the tooltip */
    }
</style>
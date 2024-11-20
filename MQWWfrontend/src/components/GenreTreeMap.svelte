<script>
    import * as d3 from "d3";
    import {BASE_URL} from "../constants.js";

    export let allPoemsIDs = []; // 从外部传递的诗歌 ID 数组
    export let width;
    export let height;
    let treemapData = null; // 存储后端返回的 Treemap 数据
    let svg, tooltip;

    let pixelWidth, pixelHeight;

    // const width = 800;
    // const height = 600;

    // 从后端获取分类数据
    async function fetchTreemapData() {
        try {
            const response = await fetch(`${BASE_URL}/getgenre/`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(allPoemsIDs)
            });
            treemapData = await response.json();
            // console.log(treemapData)
            drawTreemap();
        } catch (error) {
            console.error("Error fetching treemap data:", error);
        }
    }

    // 绘制 Treemap
    function drawTreemap() {
        if (!treemapData) return;

        // 清空之前的内容
        if (svg) d3.select(".treemap").selectAll("*").remove();
        // svg.selectAll("*").remove();
        // 创建 SVG 容器
        if (!svg) {
            svg = d3.select(".treemap")
                .attr("width", pixelWidth)
                .attr("height", pixelHeight * 0.9);
        }


        // 设置 Treemap 布局
        const root = d3
            .hierarchy(treemapData)
            .sum(d => d.value) // 计算每个节点的值
            .sort((a, b) => b.value - a.value);

        const treemapLayout = d3.treemap()
            .size([pixelWidth, pixelHeight * 0.6])
            .paddingInner(2);

        treemapLayout(root);

        // 创建颜色比例尺
        const colorScale = d3.scaleOrdinal()
            .domain(root.children.map(d => d.data.name))
            .range(d3.schemeSet3);

        // 设置最小节点显示大小
        const minRectSize = 4;

        // 绘制每个节点
        const nodes = svg
            .selectAll("g")
            .data(root.leaves())
            .join("g")
            .attr("transform", d => `translate(${d.x0}, ${d.y0})`);

        nodes
            .append("rect")
            .attr("class", "treemap-rect")
            .attr("width", d => Math.max(d.x1 - d.x0, minRectSize)) // 最小宽度
            .attr("height", d => Math.max(d.y1 - d.y0, minRectSize)) // 最小高度
            .attr("fill", d => {
                // 如果是 `unknown` 节点，直接使用其分类颜色
                return d.data.name === "unknown" ? colorScale("unknown") : colorScale(d.parent.data.name);
            })
            .attr("stroke", "#fff")
            .on("mouseover", handleMouseOver)
            .on("mouseout", handleMouseOut);


        // nodes
        //     .append("text")
        //     .attr("class", "treemap-text")
        //     .attr("x", 4)
        //     .attr("y", 14)
        //     .text(d => d.data.name);

        const legendContainer = d3.select(".legend-container").html(""); // 清空之前的内容
        const categories = root.children.map(d => d.data.name);
        const legend = legendContainer
            .selectAll(".legend-item")
            .data(categories)
            .join("div")
            .attr("class", "legend-item")
            .style("display", "inline-block")
        // .style("margin-right", "20px");

        legend
            .append("div")
            .style("width", "18px")
            .style("height", "18px")
            .style("background-color", d => colorScale(d))
            .style("display", "inline-block")
            .style("vertical-align", "middle")
            .style("margin-right", "6px");

        legend
            .append("span")
            .text(d => d)
            .style("font-size", "12px");


        // 添加 Tooltip
        tooltip = d3
            .select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background", "#fff")
            .style("border", "1px solid #ccc")
            .style("padding", "8px")
            .style("display", "none")
            .style("pointer-events", "none");

        function handleMouseOver(event, d) {
            // 获取窗口宽度
            const windowWidth = window.innerWidth;
            const tooltipWidth = 120; // Tooltip 的宽度估算值

            // 动态计算 Tooltip 的位置
            const tooltipX =
                event.pageX + 10 + tooltipWidth > windowWidth
                    ? event.pageX - tooltipWidth - 10 // 如果超出右边界，放到鼠标左侧
                    : event.pageX + 10; // 默认在鼠标右侧

            const tooltipY = event.pageY + 10;

            tooltip
                .style("display", "block")
                .html(
                    `<strong>${d.data.name}</strong><br>Count: ${d.value}<br>Category: ${
                        d.parent ? d.parent.data.name : d.data.name
                    }`
                )
                .style("left", `${tooltipX}px`)
                .style("top", `${tooltipY}px`);
        }

        function handleMouseOut() {
            tooltip.style("display", "none");
        }
    }

    // 监听 poemIDs 变化，获取数据
    $: if (allPoemsIDs.length > 0) {
        fetchTreemapData();
    }
</script>

<style>
    .treemap-rect {
        transition: fill 0.3s ease;
    }

    .treemap-rect:hover {
        fill: aquamarine;
    }

    .treemap-text {
        font-size: 10px;
        pointer-events: none;
    }

    .tooltip {
        font-size: 14px;
        color: #333;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .legend-container {
        display: flex;
        flex-wrap: wrap;
        /*margin-top: 1%;*/
        gap: 10px;
    }

    .legend-item {
        display: flex;
        align-items: center;
    }

    .treemap {
        display: block;
        overflow: visible; /* Ensures that nothing is hidden */
    }
</style>

<div bind:clientHeight={pixelHeight} bind:clientWidth={pixelWidth} style="height: {height};width:{width}">
    <svg class="treemap" width="100%" height="90%"></svg>
    <div class="legend-container"></div>
</div>
<script>
    import * as d3 from "d3";
    import {BASE_URL, roleColor, roles} from "../constants.js";

    export let poetID;
    export let width;
    export let height;
    let nodes = [];
    let links = [];
    let pixelWidth, pixelHeight;
    let svg, tooltip;
    let works;

    // 获取数据
    async function fetchWorkData() {
        const response = await fetch(`${BASE_URL}/getpoetwork/${poetID}`);
        works = await response.json();
        console.log(works)
        // 构建节点和连线
        nodes = [{id: poetID, name: `Poet ${poetID}`, group: "poet"}];
        links = [];

        works.forEach(work => {
            if (!nodes.find(node => node.id === work.workID)) {
                nodes.push({
                    id: work.workID,
                    title: work.TitleHZ,
                    group: "work"
                });
            }


            links.push({
                source: poetID,
                target: work.workID,
                role: work.role
            });


        });
        console.log(links)
        drawGraph();
    }

    // 绘制图
    function drawGraph() {
        if (!svg) {
            svg = d3.select("#relation-graph")
                .attr("width", '100%')
                .attr("height", '90%');

            // 添加缩放和拖拽功能
            svg.call(
                d3.zoom()
                    .scaleExtent([0.5, 2]) // 缩放范围
                    .on("zoom", (event) => {
                        svg.select("g").attr("transform", event.transform);
                    })
            );
        } else {
            svg.selectAll("*").remove(); // 清空内容
        }


        const container = svg.append("g");


        // 创建力导向图
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(pixelWidth / 2, pixelHeight / 4))
            .on("tick", ticked);

        // 绘制线条
        const link = container.append("g")
            .selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("stroke", d => roleColor(d.role))
            .attr("stroke-width", 2)
            .on("mouseover", handleLinkMouseOver)
            .on("mouseout", handleMouseOut);

        // 绘制节点
        const node = container.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("r", 10)
            .attr("fill", d => (d.group === "poet" ? "#e377c2" : "#1f77b4"))
            .call(d3.drag()
                .on("start", dragStarted)
                .on("drag", dragged)
                .on("end", dragEnded))
            .on("mouseover", handleNodeMouseOver)
            .on("mouseout", handleMouseOut);

        // 添加 Tooltip
        tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background-color", "white")
            .style("border", "1px solid #ddd")
            .style("padding", "8px")
            .style("border-radius", "4px")
            .style("box-shadow", "0 4px 8px rgba(0, 0, 0, 0.1)")
            .style("display", "none");

        // 更新位置
        function ticked() {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        }

        function handleNodeMouseOver(event, d) {
            if (d.group === "work") {
                tooltip
                    .style("display", "block")
                    .html(`<strong>Title:</strong> ${d.title}`)
                    .style("left", `${event.pageX + 10}px`)
                    .style("top", `${event.pageY + 10}px`);
            }
        }

        function handleLinkMouseOver(event, d) {
            tooltip
                .style("display", "block")
                .html(`
                    <strong>Work:</strong> ${d.target.title}<br>
                    <strong>Role:</strong> ${d.role || "N/A"}
                `)
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY + 10}px`);
        }

        function handleMouseOut() {
            tooltip.style("display", "none");
        }

        function dragStarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragEnded(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // 绘制图例
        drawLegend();
    }

    function drawLegend() {
        const legendContainer = d3.select("#legend1");
        if (legendContainer.empty()) {
            console.error("Legend container not found!");
            return;
        }

        legendContainer.selectAll("*").remove();

        const legend = legendContainer
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const nodeColors = [
            {label: "Work Node", color: "#1f77b4"},
            {label: "Poet Node", color: "#e377c2"}
        ];

        const roleColors = roles.map((role) => ({label: role, color: roleColor(role)}));

        // 横排显示节点颜色
        const nodeLegend = legend.append("g").attr("transform", "translate(10, 20)");
        nodeLegend
            .selectAll("g")
            .data(nodeColors)
            .enter()
            .append("g")
            .attr("transform", (d, i) => `translate(${i * 100}, 0)`)
            .each(function (d) {
                const g = d3.select(this);

                g.append("circle")
                    .attr("cx", 10)
                    .attr("cy", 10)
                    .attr("r", 8)
                    .attr("fill", d.color);

                g.append("text")
                    .attr("x", 30)
                    .attr("y", 15)
                    .attr("font-size", "12px")
                    .text(d.label);
            });

        const usedRoles = Array.from(new Set(links.map(d => d.role)));

        // 横排显示线条颜色，自动换行
        const lineColorLegend = legend.append("g").attr("transform", "translate(10, 50)");
        const lineColorData = usedRoles.map((role) => ({
            label: role,
            color: roleColor(role),
            dash: "0"
        }));

        const roleLegendWidth = 300; // 图例总宽度
        const roleItemWidth = 95; // 每个角色图例的宽度
        lineColorLegend
            .selectAll("g")
            .data(lineColorData)
            .enter()
            .append("g")
            .attr(
                "transform",
                (d, i) =>
                    `translate(${(i % Math.floor(roleLegendWidth / roleItemWidth)) * roleItemWidth}, ${
                        Math.floor(i / Math.floor(roleLegendWidth / roleItemWidth)) * 30
                    })`
            )
            .each(function (d) {
                const g = d3.select(this);

                g.append("line")
                    .attr("x1", 0)
                    .attr("y1", 10)
                    .attr("x2", 30)
                    .attr("y2", 10)
                    .attr("stroke", d.color)
                    .attr("stroke-width", 2)
                    .attr("stroke-dasharray", d.dash);

                g.append("text")
                    .attr("x", 40)
                    .attr("y", 15)
                    .attr("font-size", "12px")
                    .text(d.label);
            });
    }

    $: if (poetID) {
        fetchWorkData();
    }
</script>

<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="width: {width}; height: {height};">
    <!--    <svg id="relation-graph" style="border: 1px solid #ddd;"></svg>-->
    <!--    <div id="legend1"></div>-->
    <table style="width: 100%; border-collapse: collapse; text-align: left; border: 1px solid #ddd;">
        <thead>
        <tr>
            <th style="border: 1px solid #ddd; padding: 8px;">Title</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Role</th>
        </tr>
        </thead>
        <tbody>
        {#each works as work}
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {work.TitleHZ.split(/[:：﹕(,]/)[0].trim()}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    {work.role || 'N/A'}
                </td>
            </tr>
        {/each}
        </tbody>
    </table>
</div>
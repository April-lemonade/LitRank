<script>
    import * as d3 from "d3";
    import {BASE_URL, roleColor, roles} from "../constants.js";
    import {onMount} from "svelte";

    export let width = 800; // 默认宽度
    export let height = 600; // 默认高度
    export let workID;

    let poets = [];
    let nodes = [];
    let links = [];
    let svg;
    let pixelWidth, pixelHeight;
    let legendContainer;

    // 所有可能的角色
    // const roles = [
    //     "像贊作者", "校註者", "輓詞作者", "題辭", "序作者", "年譜作者", "傳記作者", "跋作者",
    //     "作者", "校閲", "None", "其他作者", "附記作者", "凡例作者", "墓志詺作者", "编輯", "主要作者"
    // ];

    // 为角色分配颜色
    // const roleColor = d3.scaleOrdinal()
    //     .domain(roles)
    //     .range(d3.schemeTableau10.concat(d3.schemeSet3));

    // 获取数据
    function getPoets() {
        fetch(`${BASE_URL}/getworkpoetsidwithrelation/${workID.toString()}`)
            .then(response => response.json())
            .then(poetsWithRelation => {
                poets = poetsWithRelation;
                console.log("poets", poets);
                nodes = [
                    {id: workID, group: 'work', name: `Work ${workID}`}
                ];
                links = [];

                poets.forEach((poet, index) => {
                    // 添加作者节点
                    if (!nodes.find(node => node.id === poet.poetID)) {
                        nodes.push({
                            id: poet.poetID,
                            poetId: poet.poetID,
                            group: poet.poetID,
                            name: poet.NameHZ || `Poet ${poet.poetID}`,
                            sex: poet.Sex,
                            relation: poet.relation,
                            role: poet.role
                        });
                    }

                    // 添加连线，角色存储在 link.role 中
                    links.push({
                        source: workID,
                        target: poet.poetID,
                        role: poet.role
                    });
                });

                const validNodes = nodes.filter(node => node.relation !== null && node.group !== 'work');
                // 对 validNodes 按 relation 排序，将非 suspicious 的关系排在前面
                validNodes.sort((a, b) => {
                    if (a.relation === 'suspicious' && b.relation !== 'suspicious') {
                        return 1; // a 在后
                    } else if (a.relation !== 'suspicious' && b.relation === 'suspicious') {
                        return -1; // b 在后
                    } else {
                        return 0; // 顺序不变
                    }
                });
                // console.log(validNodes)
                for (let i = 0; i < validNodes.length - 1; i++) {
                    const source = validNodes[i];
                    const target = validNodes[i + 1];

                    if (source.poetId !== target.poetId) {
                        links.push({
                            source: source.id,
                            target: target.id,
                            relation: target.relation,
                            role: 'relation'
                        });
                    }
                }

                drawGraph();

            })
            .catch(error => console.error('Error fetching data:', error));
    }


    function drawGraph() {
        if (!svg) {
            svg = d3.select('#relation-graph')
                .attr('width', width)
                .attr('height', pixelHeight * 0.5)
            // .call(d3.zoom().on('zoom', (event) => {
            //     svg.select('g').attr('transform', event.transform);
            // }));

            const zoomBehavior = d3.zoom()
                .on('zoom', (event) => {
                    console.log(event.transform)
                    svg.select('g').attr('transform', event.transform); // 应用缩放
                });

            // 应用缩放行为到 SVG
            svg.call(zoomBehavior);
        } else {
            svg.selectAll('*').remove();
        }

        const container = svg.append('g').attr("transform", 'translate(45,55) scale(0.6)');

        // 按 role 对 links 分组
        const groupedLinks = d3.group(links, d => d.role);

        // 按 groupedLinks 对 nodes 排序
        const roleToNodes = new Map();
        groupedLinks.forEach((groupLinks, role) => {
            const roleNodes = new Set();
            groupLinks.forEach(link => {
                roleNodes.add(link.source.id);
                roleNodes.add(link.target.id);
            });
            roleToNodes.set(role, Array.from(roleNodes));
        });

        // 按 role 对 nodes 排序
        nodes = nodes.sort((a, b) => {
            const aRoleIndex = Array.from(roleToNodes.values()).findIndex(nodes => nodes.includes(a.id));
            const bRoleIndex = Array.from(roleToNodes.values()).findIndex(nodes => nodes.includes(b.id));
            return aRoleIndex - bRoleIndex;
        });

        // 为 role 创建中心点
        const roleCenters = {};
        Array.from(groupedLinks.keys()).forEach((role, i) => {
            roleCenters[role] = {
                x: (pixelWidth / 2) + i * 150, // 每组横向偏移
                y: pixelHeight / 4
            };
        });

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(pixelWidth / 2, pixelHeight / 4))
            .force('cluster', forceCluster(roleCenters))
            .on('tick', ticked);

        const link = container.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', d => roleColor(d.role))
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', d => d.relation === 'suspicious' ? '5,5' : '0')
            .on('mouseover', mouseOverLink)
            .on('mouseout', mouseOut);

        const node = container.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', 10)
            .attr('fill', d => d.sex === '男' ? '#1f77b4' : (d.sex === '女' ? '#e377c2' : '#6AABD2'))
            .call(d3.drag()
                .on('start', dragStarted)
                .on('drag', dragged)
                .on('end', dragEnded))
            .on('mouseover', mouseOverNode)
            .on('mouseout', mouseOut);

        const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('background-color', 'white')
            .style('border', '1px solid #ddd')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('box-shadow', '0 4px 8px rgba(0, 0, 0, 0.1)');

        function forceCluster(centers) {
            return (alpha) => {
                nodes.forEach(node => {
                    const role = links.find(link => link.source.id === node.id || link.target.id === node.id)?.role;
                    if (role && centers[role]) {
                        node.vx += (centers[role].x - node.x) * alpha * 0.1;
                        node.vy += (centers[role].y - node.y) * alpha * 0.1;
                    }
                });
            };
        }

        function ticked() {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
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

        function mouseOverNode(event, d) {
            const tooltipWidth = 120;
            const pageWidth = window.innerWidth;

            let leftPosition = event.pageX + 10;
            if (event.pageX + tooltipWidth + 10 > pageWidth) {
                leftPosition = event.pageX - tooltipWidth - 10;
            }

            tooltip
                .style('display', 'block')
                .html(`
            <strong>Name:</strong> ${d.name}<br>
            <strong>Role:</strong>${d.role}<br>
            <strong>Relation to Main Author:</strong> ${d.relation || 'unknown'}<br>
        `)
                .style('left', `${leftPosition}px`)
                .style('top', `${event.pageY + 10}px`);
        }

        function mouseOverLink(event, d) {
            const tooltipWidth = 120;
            const pageWidth = window.innerWidth;

            let leftPosition = event.pageX + 10;
            if (event.pageX + tooltipWidth + 10 > pageWidth) {
                leftPosition = event.pageX - tooltipWidth - 10;
            }

            if (d.source.id === workID) {
                // Poet 和 Work 之间的链接
                tooltip
                    .style('display', 'block')
                    .html(`
            <strong>Poet:</strong> ${d.target.name}<br>
            <strong>Role:</strong> ${d.role || 'N/A'}<br>
        `)
                    .style('left', `${leftPosition}px`)
                    .style('top', `${event.pageY + 10}px`);
            } else {
                // Poet 和 Poet 之间的链接
                //         tooltip
                //             .style('display', 'block')
                //             .html(`
                //     <strong>Poet:</strong> ${d.target.name}<br>
                //     <strong>Relation to Main Author:</strong> ${d.relation || 'N/A'}<br>
                // `)
                //             .style('left', `${leftPosition}px`)
                //             .style('top', `${event.pageY + 10}px`);
            }
        }

        function mouseOut() {
            tooltip.style('display', 'none');
        }
    }


    $: if (workID) {
        getPoets();
        // drawLegend()
    }

    // $:drawLegend();

    onMount(() => {
        legendContainer = d3.select("#legend1");
        console.log('Legend container:', legendContainer.node());
        drawLegend();
    })

    function drawLegend() {
        const legendContainer = d3.select("#legend1");
        if (legendContainer.empty()) {
            console.error("Legend container not found!");
            return;
        }

        legendContainer.selectAll("*").remove();

        const legend = legendContainer
            .append("svg")
            .attr("width", 300)
            .attr("height", 300);

        const nodeColors = [
            {label: "Male Node", color: "#1f77b4"},
            {label: "Female Node", color: "#e377c2"}
        ];

        const lineStyles = [
            {label: "kinship", color: "#ff7f0e", dash: "0"},
            {label: "suspicious kinship", color: "#ff7f0e", dash: "5,5"}
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

        // 横排显示线条样式
        const lineStyleLegend = legend.append("g").attr("transform", "translate(10, 60)");
        lineStyleLegend
            .selectAll("g")
            .data(lineStyles)
            .enter()
            .append("g")
            .attr("transform", (d, i) => `translate(${i * 120}, 0)`)
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

        const usedRoles = Array.from(new Set(links.map(d => d.role))).filter(Boolean);

        // 横排显示线条颜色，自动换行
        const lineColorLegend = legend.append("g").attr("transform", "translate(10, 100)");
        const lineColorData = roles.map((role) => ({
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

</script>

<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="width: {width}; height: {height};">
    <svg id="relation-graph" style="border: 1px solid #ddd;"></svg>
    <div id="legend1" style="width: {width}; height: {height};"></div>
</div>


<style>
    svg {
        display: block;
        margin: 0 auto;
    }

    .tooltip {
        font-size: 14px;
        color: #333;
        pointer-events: none;
    }

    #legend {
        margin-top: 20px;
        display: block;
    }
</style>
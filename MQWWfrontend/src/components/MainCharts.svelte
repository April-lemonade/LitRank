<script>
    import * as d3 from "d3";
    import {BASE_URL} from "../constants.js";
    import {onMount} from "svelte";
    import geojsonData from '../assets/provinceGeojson.json';
    import * as turf from "@turf/turf";


    let pixelWidth, pixelHeight;
    export let rank;
    export let poetRank;
    export let selectContent;
    export let clear;

    // 方框的尺寸
    const boxWidth = 40;
    let scatterData, poetScatterData;
    let unknownWorkData = [], unknownPoetData = []; // 存储无效数据
    let xScaleWork, xScalePoet, yScaleWork, yScalePoet, unknownWorkXScale, unknownPoetXScale;
    const margin = {top: 25, right: 10, bottom: 30, left: 60};
    export let selectedWorkID = -1
    export let selectedPoetID = -1;
    let heighlightWork = [], heighlightPoet = [];
    let workYearElement, poetYearElement, poetRegionElement; // SVG 容器引用

    let tooltipContent = ""; // 工具提示的内容
    let tooltipStyle = {left: "0px", top: "0px", display: "none"}; // 工具提示样式
    let hierarchyData;
    let regions;
    let packedRegions;
    let projection;
    let pathGenerator;
    let isMouseInSVG = false;


    onMount(() => {
        const svg = d3.select(poetRegionElement);
        const g = svg.select("#poetRegionMap"); // 地图路径组

        const zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on("zoom", (event) => {

                const {transform} = event;

                // 对应调整 Packed Circle 的位置
                g.attr("transform", transform); // 地图本身
                packedRegions.forEach(region => {
                    region.packedData.descendants().forEach(node => {
                        node.x = (node.x * transform.k) + transform.x;
                        node.y = (node.y * transform.k) + transform.y;
                    });
                });
            });


        svg.call(zoom);

        regions = geojsonData.features.map(feature => ({
            name: feature.properties.name.replace(/市|县|区$/, ""),
            parent: feature.properties.parent || null,
            coordinates: feature.properties.center
        }));

        geojsonData.features.forEach(feature => {
            const originalName = feature.properties.name;
            if (originalName && originalName.length > 1) {
                feature.properties.name = originalName.slice(0, 2);
            }
        });


        // console.log(geojsonData)

    })
    let mapdata;

    $:if (workYearElement && poetYearElement) {
        document.addEventListener('mousemove', (event) => {
            const svgBounds = workYearElement.getBoundingClientRect();
            const poetBounds = poetYearElement.getBoundingClientRect();

            // 检查鼠标是否在任何一个 SVG 内部
            isMouseInSVG =
                (event.clientX >= svgBounds.left &&
                    event.clientX <= svgBounds.right &&
                    event.clientY >= svgBounds.top &&
                    event.clientY <= svgBounds.bottom) ||
                (event.clientX >= poetBounds.left &&
                    event.clientX <= poetBounds.right &&
                    event.clientY >= poetBounds.top &&
                    event.clientY <= poetBounds.bottom);
        });
    }

    $:if (geojsonData) {
        mapdata = geojsonData
        mapdata.features = mapdata.features.map(feature => turf.rewind(feature, {reverse: true}));
        // 设置地图投影
        projection = projection = d3.geoMercator()
            .center([104, 35]) // 设置全国中心经纬度
            .scale(pixelWidth * 0.8)
            .translate([pixelWidth / 2, pixelHeight / 6]); // 偏移至 SVG 中心

        // 创建路径生成器
        pathGenerator = d3.geoPath().projection(projection);

        geojsonData.features.forEach(feature => {
            const path = pathGenerator(feature);
            // console.log("Path:", path);
        });
    }

    const pack = d3
        .pack()
        .size([50, 50]) // 每个地区的 circle packing 大小
        .padding(0); // 节点间距


    let regionCircles = [];

    function showTooltip(event, points) {
        tooltipContent = points.map(d => ({
            text: d.TitleHZ
                ? d.TitleHZ.split(/[:：﹕(,]/)[0].trim() // 提取 TitleHZ 前缀部分并去掉多余空格
                : d.NameHZ || "Unknown", // 如果没有 TitleHZ，则用 NameHZ 或默认值
            data: d,
            type: d.workID ? 'work' : 'poet'
        }));
        tooltipStyle = {
            left: `${event.pageX - 120}px`,
            top: `${event.pageY}px`,
            display: "block"
        };
    }

    function handlePointClick(data) {
        // console.log("Clicked on:", data);
        if (data.workID) {
            selectWork(data);
        } else {
            selectPoet(data);
        }
        // 在这里处理点击事件，比如显示详细信息等
    }

    $:{
        if (selectedWorkID !== -1) {
            const connectionContainer = d3.select("#connections");
            connectionContainer?.selectAll("line").remove(); // 清除旧连线
            // let temp = {workID: selectedWorkID, poetID: selectedPoetID}
            selectedPoetID = -1
            heighlightWork = [selectedWorkID]
            fetch(`${BASE_URL}/getworkpoetsidwithrelation/${selectedWorkID}`)
                .then(response => response.json())
                .then(results => {
                    // console.log(results)
                    let poets = results.map(d => d.poetID)
                    // console.log(poets)
                    heighlightPoet = poets.sort((a, b) => {
                        const poetA = poetScatterData.find(p => p.poetID === a);
                        const poetB = poetScatterData.find(p => p.poetID === b);
                        return (poetA?.poetStartYear || 0) - (poetB?.poetStartYear || 0);
                    });
                    drawConnections();
                })
            if (selectContent) selectContent({work: selectedWorkID, poet: selectedPoetID})
        }

        if (selectedPoetID !== -1) {
            const connectionContainer = d3.select("#connections");
            connectionContainer?.selectAll("line").remove(); // 清除旧连线
            selectedWorkID = -1;
            heighlightPoet = [selectedPoetID]
            // if (selectedPoetID)
            fetch(`${BASE_URL}/getpoetworkID/${selectedPoetID}`)
                .then(response => response.json())
                .then(results => {
                    // console.log(results)
                    let works = results.map(d => d.workID)
                    // console.log(poets)
                    heighlightWork = works.sort((a, b) => {
                        const workA = scatterData.find(p => p.workID === a);
                        const workB = scatterData.find(p => p.workID === b);
                        return (workA?.PubStartYear || 0) - (workB?.PubStartYear || 0);
                    });

                })
            if (selectContent) selectContent({work: selectedWorkID, poet: selectedPoetID})
        }
    }

    function selectWork(data) {
        // if (data.overlapping) return;
        selectedWorkID = selectedWorkID === data.workID ? -1 : data.workID;
        if (selectedWorkID === -1) {
            heighlightWork = []
            heighlightPoet = []
            d3.select("#connections").selectAll("line").remove(); // 移除连线
        } else {
            selectedPoetID = -1
            // 获取原生 DOM 元素数组
            const selectedCircle = d3.selectAll(".workCircle")._groups[0];

            // 过滤出符合条件的元素
            const filteredCircle = Array.from(selectedCircle).filter(d =>
                d.__attributes && d.__attributes["data-workid"] === selectedWorkID
            );

            // 如果找到了目标元素
            if (filteredCircle.length > 0) {
                const targetElement = filteredCircle[0];

                // 将目标元素转换为 D3 selection 以便使用 D3 的方法
                d3.select(targetElement).raise();

                console.log("Raised element:", targetElement);
            } else {
                console.log("No matching element found");
            }
            heighlightWork = [selectedWorkID];
            // if (selectedPoetID === -1) {
            //     heighlightWork = [selectedWorkID]
            // } else {
            //     if (!heighlightWork.includes(selectedWorkID))
            //         heighlightWork = [...heighlightWork, selectedWorkID];
            // }
            fetch(`${BASE_URL}/getworkpoetsidwithrelation/${selectedWorkID}`)
                .then(response => response.json())
                .then(results => {
                    // console.log(results)
                    let poets = results.map(d => d.poetID)
                    // console.log(poets)
                    heighlightPoet = poets.sort((a, b) => {
                        const poetA = poetScatterData.find(p => p.poetID === a);
                        const poetB = poetScatterData.find(p => p.poetID === b);
                        return (poetA?.poetStartYear || 0) - (poetB?.poetStartYear || 0);
                    });

                    drawConnections();
                })
        }
        if (selectContent) selectContent({work: selectedWorkID, poet: selectedPoetID})
        // console.log(data)
    }

    function selectPoet(data) {
        const connectionContainer = d3.select("#connections");
        connectionContainer?.selectAll("line").remove(); // 清除旧连线
        selectedPoetID = selectedPoetID === data.poetID ? -1 : data.poetID;
        if (selectedPoetID === -1) {
            heighlightPoet = [];
            heighlightWork = []
        } else {
            const selectedCircle = d3.selectAll(".poetCircle").filter(d => d.poetID === selectedPoetID);
            selectedCircle.raise(); // 将高亮的点移动到顶层
            selectedWorkID = -1;
            heighlightPoet = [selectedPoetID]
            // if (selectedPoetID)
            fetch(`${BASE_URL}/getpoetworkID/${selectedPoetID}`)
                .then(response => response.json())
                .then(results => {
                    // console.log(results)
                    let works = results.map(d => d.workID)
                    // console.log(poets)
                    heighlightWork = works.sort((a, b) => {
                        const workA = scatterData.find(p => p.workID === a);
                        const workB = scatterData.find(p => p.workID === b);
                        return (workA?.PubStartYear || 0) - (workB?.PubStartYear || 0);
                    });
                })
        }
        if (selectContent) selectContent({work: selectedWorkID, poet: selectedPoetID})

        // console.log(data)
    }

    function hideTooltip() {
        tooltipStyle.display = "none";
    }

    // 初始化缩放行为
    function setupZoom(svg, xScale, yScale, setTransform) {
        hideTooltip();
        const zoom = d3.zoom()
            .scaleExtent([1, 10]) // 缩放范围
            .translateExtent([[0, 0], [pixelWidth, pixelHeight / 2]]) // 限制平移范围
            .on("zoom", (event) => {
                const connectionContainer = d3.select("#connections");
                connectionContainer?.selectAll("line").remove(); // 清除旧连线
                hideTooltip();
                const transform = event.transform;

                // 更新比例尺
                const newXScale = transform.rescaleX(xScale);
                const newYScale = transform.rescaleY(yScale);

                // 设置新的比例尺
                setTransform({xScale: newXScale, yScale: newYScale});

                // 更新轴线
                svg.select(".x-axis").call(d3.axisBottom(newXScale));
                svg.select(".y-axis").call(d3.axisLeft(newYScale).ticks(4));

            });


        // 应用缩放行为到 SVG
        svg.call(zoom);
    }

    // 比例尺重计算触发点
    let workTransform = {xScale: null, yScale: null};
    let poetTransform = {xScale: null, yScale: null};


    // 将诗人数据按照地区分组
    function groupByRegion(data) {
        const regions = {};
        const unknownRegion = [];

        data.forEach((poet) => {
            const region = poet.poetDetail.fullRegion || "unknown";
            const poetData = {
                name: poet.poetDetail.NameHZ,
                weight: poet.poetCount.normalized_totalWeight,
                poetID: poet.poetID
            };

            if (region === "unknown") {
                unknownRegion.push(poetData);
            } else {
                if (!regions[region]) {
                    regions[region] = [];
                }
                regions[region].push(poetData);
            }
        });

        // 转换为层次化数据，不包含 unknown
        const result = {
            name: "root",
            children: Object.entries(regions).map(([region, poets]) => ({
                name: region,
                children: poets
            }))
        };

        return result; // 返回层次化数据和 unknown 数据
    }


    $: if (rank && poetRank && pixelWidth) {
        // 计算每个图表的高度
        const numCharts = 3; // 当前有两个图表
        const chartHeight = pixelHeight / numCharts;

        hierarchyData = groupByRegion(poetRank);
        // console.log(hierarchyData)
        // 获取地区中心点
        const regionCenters = geojsonData.features.reduce((acc, feature) => {
            acc[feature.properties.name] = feature.properties.center;
            return acc;
        }, {});

        packedRegions = hierarchyData.children.map(region => {
            // 获取地区的地理中心点
            const regionCenter = regionCenters[region.name];

            if (!regionCenter) {
                console.warn(`Region center not found for: ${region.name}`);
                return null;
            }

            // 将地理中心点投影到屏幕坐标
            const projectedCenter = projection(regionCenter);

            // 使用 d3.hierarchy 创建分层数据，并计算 circle packing
            const packedData = pack(
                d3.hierarchy(region).sum(d => (d.children ? d.children.length : 1))
            );

            // 创建比例尺同步地图范围与 Circle Packing 范围
            const scaleX = d3.scaleLinear()
                .domain([packedData.x - packedData.r, packedData.x + packedData.r])
                .range([projectedCenter[0] - packedData.r, projectedCenter[0] + packedData.r]);

            const scaleY = d3.scaleLinear()
                .domain([packedData.y - packedData.r, packedData.y + packedData.r])
                .range([projectedCenter[1] - packedData.r, projectedCenter[1] + packedData.r]);

            packedData.descendants().forEach(node => {
                node.x = scaleX(node.x);
                node.y = scaleY(node.y);
            });

            return {
                name: region.name,
                center: projectedCenter, // 投影中心坐标
                packedData,              // 计算后的 circle packing 数据
            };
        }).filter(Boolean); // 过滤掉无法匹配到中心的地区

        // console.log(packedRegions)


        // 提取散点数据并过滤无效数据
        const allScatterData = rank.map(d => ({
            PubStartYear: parseInt(d.workCount.PubStartYear),
            WorkImportance: d.workCount.WorkImportance,
            TitleHZ: d.workCount.TitleHZ,
            workID: d.workID
        }));

        const allPoetScatterData = poetRank.map(d => ({
            poetStartYear: parseInt(d.poetDetail.StartYear),
            PoetImportance: d.poetCount.ln_normalized_totalWeight,
            NameHZ: d.poetDetail.NameHZ,
            poetID: d.poetID
        }));

        // 未知年份点
        unknownWorkData = rank.filter(d => !d.workCount.PubStartYear).map(d => ({
            WorkImportance: d.workCount.WorkImportance,
            TitleHZ: d.workCount.TitleHZ,
            workID: d.workID
        }));

        unknownWorkData.forEach(d => {
            d.overlapping = scatterData.filter(
                p => d.PubStartYear === p.PubStartYear && d.WorkImportance === p.WorkImportance
            ).length > 1;
        });

        unknownPoetData = poetRank.filter(d => !d.poetDetail.StartYear || d.poetDetail.StartYear === 'unknown').map(d => ({
            PoetImportance: d.poetCount.ln_normalized_totalWeight,
            NameHZ: d.poetDetail.NameHZ,
            poetID: d.poetID
        }));

        unknownPoetData.forEach(d => {
            d.overlapping = poetScatterData.filter(
                p => d.poetStartYear === p.poetStartYear && d.PoetImportance === p.PoetImportance
            ).length > 1;
        });

        // 有效数据
        scatterData = allScatterData.filter(d => d.PubStartYear);
        poetScatterData = allPoetScatterData.filter(d => d.poetStartYear && d.poetStartYear !== 'unknown');

        console.log("scatterData", scatterData);

        // 找到有重叠的点
        scatterData.forEach(d => {
            d.overlapping = scatterData.filter(
                p => d.PubStartYear === p.PubStartYear && d.WorkImportance === p.WorkImportance
            ).length > 1;
        });

        poetScatterData.forEach(d => {
            d.overlapping = poetScatterData.filter(
                p => d.poetStartYear === p.poetStartYear && d.PoetImportance === p.PoetImportance
            ).length > 1;
        });

        // 定义比例尺
        const xDomain = [
            Math.min(
                d3.min(scatterData, d => d.PubStartYear),
                d3.min(poetScatterData, d => d.poetStartYear)
            ) - 5,
            Math.max(
                d3.max(scatterData, d => d.PubStartYear),
                d3.max(poetScatterData, d => d.poetStartYear)
            ) + 5
        ];

        xScaleWork = d3.scaleLinear()
            .domain(xDomain)
            .range([margin.left, pixelWidth - margin.right]);
        xScalePoet = d3.scaleLinear()
            .domain(xDomain)
            .range([margin.left, pixelWidth - margin.right]);

        yScaleWork = d3.scaleLinear()
            .domain([d3.min(scatterData, d => d.WorkImportance), d3.max(scatterData, d => d.WorkImportance)])
            .range([chartHeight - margin.bottom, margin.top]);

        yScalePoet = d3.scaleLinear()
            .domain([d3.min(poetScatterData, d => d.PoetImportance), d3.max(poetScatterData, d => d.PoetImportance)])
            .range([chartHeight - margin.bottom, margin.top]);

        workTransform = {xScale: xScaleWork, yScale: yScaleWork};
        poetTransform = {xScale: xScalePoet, yScale: yScalePoet};

        // 初始化轴线
        const workYear = d3.select(workYearElement);
        const poetYear = d3.select(poetYearElement);

        workYear.selectAll(".x-axis")
            .data([null])
            .join("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0, ${chartHeight - margin.bottom})`)
            .call(d3.axisBottom(xScaleWork));

        poetYear.selectAll(".x-axis")
            .data([null])
            .join("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0, ${chartHeight - margin.bottom})`)
            .call(d3.axisBottom(xScalePoet));

        workYear.selectAll(".y-axis")
            .data([null])
            .join("g")
            .attr("class", "y-axis")
            .attr("transform", `translate(${margin.left}, 0)`)
            .call(d3.axisLeft(yScaleWork).ticks(4));

        poetYear.selectAll(".y-axis")
            .data([null])
            .join("g")
            .attr("class", "y-axis")
            .attr("transform", `translate(${margin.left}, 0)`)
            .call(d3.axisLeft(yScalePoet).ticks(4));

        // 调用缩放行为函数
        setupZoom(workYear, xScaleWork, yScaleWork, (newTransform) => workTransform = newTransform);
        setupZoom(poetYear, xScalePoet, yScalePoet, (newTransform) => poetTransform = newTransform);
    }

    $:{
        if (clear) {
            const connectionContainer = d3.select("#connections");
            connectionContainer?.selectAll("line").remove(); // 清除旧连线
            selectedWorkID = -1;
            selectedPoetID = -1;
            heighlightPoet = [];
            heighlightWork = [];
        }
    }

    function drawConnections() {
        const connectionContainer = d3.select("#connections");
        connectionContainer.selectAll("line").remove(); // 清除旧连线

        if (selectedWorkID !== -1) {
            heighlightPoet.forEach(poetID => {
                // 查找 work 和 poet 数据，包括 unknown 数据
                const workNode = scatterData.find(d => d.workID === selectedWorkID) ||
                    unknownWorkData.find(d => d.workID === selectedWorkID);

                const poetNode = poetScatterData.find(d => d.poetID === poetID) ||
                    unknownPoetData.find(d => d.poetID === poetID);

                if (workNode && poetNode) {
                    const workCoords = workNode.PubStartYear
                        ? {
                            x: workTransform.xScale(workNode.PubStartYear),
                            y: workTransform.yScale(workNode.WorkImportance)
                        }
                        : {
                            x: margin.left - boxWidth / 2, // 未知年份的坐标
                            y: workTransform.yScale(workNode.WorkImportance)
                        };

                    const poetCoords = poetNode.poetStartYear
                        ? {
                            x: poetTransform.xScale(poetNode.poetStartYear),
                            y: poetTransform.yScale(poetNode.PoetImportance)
                        }
                        : {
                            x: margin.left - boxWidth / 2, // 未知年份的坐标
                            y: poetTransform.yScale(poetNode.PoetImportance)
                        };

                    // 转换为 connections 的 SVG 坐标
                    const workSvgRect = workYearElement.getBoundingClientRect();
                    const poetSvgRect = poetYearElement.getBoundingClientRect();
                    const connectionsSvgRect = connectionContainer.node().getBoundingClientRect();

                    const workSvgOffset = {
                        x: workSvgRect.left - connectionsSvgRect.left,
                        y: workSvgRect.top - connectionsSvgRect.top
                    };
                    const poetSvgOffset = {
                        x: poetSvgRect.left - connectionsSvgRect.left,
                        y: poetSvgRect.top - connectionsSvgRect.top
                    };

                    connectionContainer
                        .append("line")
                        .attr("x1", workCoords.x + workSvgOffset.x)
                        .attr("y1", workCoords.y + workSvgOffset.y)
                        .attr("x2", poetCoords.x + poetSvgOffset.x)
                        .attr("y2", poetCoords.y + poetSvgOffset.y)
                        .attr("stroke", "steelblue")
                        .attr("stroke-width", 1.5);
                }
            });
        }
    }
</script>

<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="width: 100%;height: 100%">
    <!-- Tooltip -->
    <div class="tooltip"
         style="position: absolute; pointer-events: auto; background: #fff; border: 1px solid #ccc; padding: 5px;
            border-radius: 5px;max-width: 200px;min-width: 150px;
            display: {tooltipStyle.display}; left: {tooltipStyle.left}; top: {tooltipStyle.top};">
        {#if tooltipContent.length > 0}
            <ul>
                {#each tooltipContent as item}
                    <span onclick={() => handlePointClick(item.data)}
                          style="cursor: pointer; margin-right: 10px; color: steelblue; text-decoration: underline;">
                        {item.text}
                    </span>
                {/each}
            </ul>
        {/if}
    </div>
    <svg id="connections"
         style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></svg>
    <svg bind:this={workYearElement} width="100%" height="34%" onmouseleave={() => {
        setTimeout(() => {
            if (!isMouseInSVG) hideTooltip();
        }, 100); // 100ms 延迟
    }}>
        <text x="50%" y="98%" text-anchor="middle" font-size="12px">Publication Year</text>
        <text x="10%" y="5%" text-anchor="middle" transform="rotate(0, 20, 50)" font-size="12px">Work Popularity</text>

        <g id="unknownWorkData">
            {#each unknownWorkData as d}
                <circle
                        class="workCircle"
                        cx={margin.left - boxWidth / 2}
                        cy={workTransform.yScale(d.WorkImportance)}
                        r="3"
                        fill={d.overlapping ? "darkblue" : "steelblue"}
                        fill-opacity={heighlightWork.length === 0 || heighlightWork.includes(d.workID) ? 1 : 0.1}
                        opacity={selectedPoetID !== -1 && !heighlightWork.includes(d.workID) ? 0 : 1}
                        pointer-events={selectedPoetID !== -1 && !heighlightWork.includes(d.workID) ? "none" : "auto"}
                        filter={heighlightWork.length === 0 || heighlightWork.includes(d.workID) ? "" : "grayscale(100%)"}
                        stroke="white"
                        stroke-width="1.5"
                        data-workid={d.workID}
                        onmouseover={(e) => {
                        const overlappingPoints = unknownWorkData.filter(p =>
                                        workTransform.yScale(p.WorkImportance) === workTransform.yScale(d.WorkImportance));
                        showTooltip(e, overlappingPoints.length > 0 ? overlappingPoints : [d]);}}
                        onclick={()=>{
                            if (d.overlapping) return;
                            selectWork(d)
                        }}
                />
            {/each}
        </g>
        <g id="WorkData">
            {#each scatterData as d}
                <circle
                        class="workCircle"
                        cx={workTransform.xScale(d.PubStartYear)}
                        cy={workTransform.yScale(d.WorkImportance)}
                        r="3"
                        fill={d.overlapping ? "darkblue" : "steelblue"}
                        fill-opacity={heighlightWork.length === 0 || heighlightWork.includes(d.workID) ? 1 : 0.1}
                        opacity={selectedPoetID !== -1 && !heighlightWork.includes(d.workID) ? 0 : 1}
                        pointer-events={selectedPoetID !== -1 && !heighlightWork.includes(d.workID) ? "none" : "auto"}
                        filter={heighlightWork.length === 0 || heighlightWork.includes(d.workID) ? "" : "grayscale(100%)"}
                        stroke="white"
                        stroke-width="1.5"
                        data-workid={d.workID}
                        onmouseover={(e) => {
                        const overlappingPoints = scatterData.filter(p =>
                                        workTransform.xScale(p.PubStartYear) === workTransform.xScale(d.PubStartYear) &&
                                        workTransform.yScale(p.WorkImportance) === workTransform.yScale(d.WorkImportance));
                        showTooltip(e, overlappingPoints.length > 0 ? overlappingPoints : [d]);}}
                        onclick={()=>selectWork(d)}
                />
            {/each}
        </g>

    </svg>
    <svg bind:this={poetYearElement} width="100%" height="34%" onmouseleave={() => {
        setTimeout(() => {
            if (!isMouseInSVG) hideTooltip();
        }, 100); // 100ms 延迟
    }}>
        <text x="50%" y="100%" text-anchor="middle" font-size="12px">Poet Start Year</text>
        <text x="10%" y="5%" text-anchor="middle" transform="rotate(0, 20, 50)" font-size="12px">Poet Popularity</text>
        <g id="unknownPoetData">
            {#each unknownPoetData as d}
                <circle
                        class="poetCircle"
                        cx={margin.left - boxWidth / 2}
                        cy={poetTransform.yScale(d.PoetImportance)}
                        r="3"
                        fill={d.overlapping ? "darkorange" : "orange"}
                        fill-opacity={heighlightPoet.length === 0 || heighlightPoet.includes(d.poetID) ? 1 : 0.1}
                        opacity={selectedWorkID !== -1 && !heighlightPoet.includes(d.poetID) ? 0 : 1}
                        pointer-events={selectedWorkID !== -1 && !heighlightPoet.includes(d.poetID) ? "none" : "auto"}
                        filter={heighlightPoet.length === 0 || heighlightPoet.includes(d.poetID) ? "" : "grayscale(100%)"}
                        stroke="white"
                        stroke-width="1.5"
                        onmouseover={(e) => {
                            let overlappingPoints = poetScatterData.filter(p =>
                                            poetTransform.xScale(p.poetStartYear) === poetTransform.xScale(d.poetStartYear) &&
                                            poetTransform.yScale(p.PoetImportance) === poetTransform.yScale(d.PoetImportance));
                            showTooltip(e, overlappingPoints.length > 0 ? overlappingPoints : [d]);}}
                        onclick={()=>selectPoet(d)}
                />
            {/each}
        </g>
        <g id="PoetData">
            {#each poetScatterData as d}
                <circle
                        class="poetCircle"
                        cx={poetTransform.xScale(d.poetStartYear)}
                        cy={poetTransform.yScale(d.PoetImportance)}
                        r="3"
                        fill={d.overlapping ? "darkorange" : "orange"}
                        fill-opacity={heighlightPoet.length === 0 || heighlightPoet.includes(d.poetID) ? 1 : 0.1}
                        opacity={selectedWorkID !== -1 && !heighlightPoet.includes(d.poetID) ? 0 : 1}
                        pointer-events={selectedWorkID !== -1 && !heighlightPoet.includes(d.poetID) ? "none" : "auto"}
                        filter={heighlightPoet.length === 0 || heighlightPoet.includes(d.poetID) ? "" : "grayscale(100%)"}
                        stroke="white"
                        stroke-width="1.5"
                        onmouseover={(e) => {
                            let overlappingPoints = poetScatterData.filter(p =>
                                            poetTransform.xScale(p.poetStartYear) === poetTransform.xScale(d.poetStartYear) &&
                                            poetTransform.yScale(p.PoetImportance) === poetTransform.yScale(d.PoetImportance));
                            showTooltip(e, overlappingPoints.length > 0 ? overlappingPoints : [d]);}}
                        onclick={()=>selectPoet(d)}
                />
            {/each}
        </g>
        <g class="poetConnections">
            <!-- 连线部分 -->
            {#if heighlightPoet.length > 0}
                <path
                        d={`
                M ${heighlightPoet
                    .map(poetID => {
                        const poetKnown = poetScatterData.find(p => p.poetID === poetID);
                        const poetUnknown = unknownPoetData.find(p => p.poetID === poetID);
                        if (poetKnown) {
                            return `${poetTransform.xScale(poetKnown.poetStartYear)} ${poetTransform.yScale(poetKnown.PoetImportance)}`;
                        } else if (poetUnknown) {
                            return `${margin.left - 20} ${poetTransform.yScale(poetUnknown.PoetImportance)}`;
                        } else {
                            return null;
                        }
                    })
                    .filter(Boolean)
                    .join(' L ')}
            `}
                        stroke="orange"
                        stroke-width="1.5"
                        fill="none"
                />
            {/if}
        </g>
    </svg>

    <svg bind:this={poetRegionElement} width='100%' height="32%">
        <g id="poetRegionMap">
            {#if geojsonData}
                {#each geojsonData.features as feature}
                    <path
                            d={pathGenerator(feature)}
                            fill="white"
                            stroke="black"
                            stroke-width="1"
                    />
                {/each}
            {/if}

            <!-- 绘制 Circle Packing -->
            {#each packedRegions as region}
                {#each region.packedData.descendants() as node}
                    <circle
                            cx={node.x}
                            cy={node.y}
                            r={node.r}
                            fill={node.children ? 'none' : '#ffdd89'}
                            stroke={node.children ? 'none' : 'white'}
                            stroke-width="0.5"
                    >
                        <title>{node.data.name || region.name}</title>
                    </circle>
                {/each}

                <!-- 显示地区名称 -->
                <!--                <text-->
                <!--                        x={region.center[0]}-->
                <!--                        y={region.center[1]}-->
                <!--                        text-anchor="middle"-->
                <!--                        font-size="14px"-->
                <!--                        font-weight="bold"-->
                <!--                >-->
                <!--                    {region.name}-->
                <!--                </text>-->
            {/each}
        </g>
    </svg>

</div>
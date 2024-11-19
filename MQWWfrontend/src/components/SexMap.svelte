<script>
    import * as d3 from "d3";
    import * as turf from "@turf/turf";
    import {onMount} from "svelte";
    import {BASE_URL} from "../constants.js";

    export let width;
    export let height;
    export let allPoetsIDs;

    let svgW = 1200; // SVG 宽度
    let svgH = 1000; // SVG 高度

    // 地图数据和性别数据
    let mapData = null;
    let genderData = [];

    // 定义颜色矩阵（3x3 双轴颜色）
    const colors = [
        "#dfdfdf", "#ace4e4", "#5ac8c8", // 第一行颜色
        "#dfb0d6", "#a5add3", "#5698b9", // 第二行颜色
        "#be64ac", "#8c62aa", "#3b4994"  // 第三行颜色
    ];

    const gridSize = 3; // 颜色矩阵的网格大小
    let svg, g; // 定义 SVG 和主分组容器

    // 加载 GeoJSON 地图数据
    async function fetchMapData() {
        try {
            const response = await fetch("https://geo.datav.aliyun.com/areas_v3/bound/100000_full_city.json");
            const data = await response.json();

            // 修复多边形坐标顺序
            data.features = data.features.map(feature => turf.rewind(feature, {reverse: true}));

            mapData = data;
            drawMap(); // 在地图数据加载后立即绘制地图
        } catch (error) {
            console.error("Error loading map data:", error);
        }
    };

    // 获取性别数据
    async function fetchGenderData() {
        if (!allPoetsIDs || allPoetsIDs.length === 0) return;

        try {
            const response = await fetch(`${BASE_URL}/getsexdistribution/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(allPoetsIDs) // 确保发送的是数组
            });
            const result = await response.json();
            genderData = result;
            // console.log(genderData);
            drawMap(); // 在性别数据加载后重新绘制地图
        } catch (error) {
            console.error("Error fetching gender data:", error);
        }
    }

    // 绘制地图
    function drawMap() {
        if (!mapData) return;

        // 创建或选择 SVG 容器
        if (!svg) {
            svg = d3.select("svg.map")
                .attr("viewBox", `0 0 ${svgW} ${svgH}`)
                .attr("width", svgW)
                .attr("height", svgH);

            g = svg.append("g").attr("class", "path-wrap");

            // 添加缩放和拖拽功能
            const zoom = d3.zoom()
                .scaleExtent([1, 10]) // 缩放比例范围
                .on("zoom", (event) => {
                    g.attr("transform", event.transform); // 应用缩放和平移
                });

            svg.call(zoom); // 应用缩放到 SVG 容器
        } else {
            g.selectAll("*").remove(); // 清空之前的内容
        }

        // 设置投影
        const projection = d3.geoMercator()
            .center([104, 35]) // 设置全国中心经纬度
            .scale(850) // 地图缩放比例
            .translate([svgW / 2, svgH / 2]); // 偏移至 SVG 中心

        const pathGenerator = d3.geoPath().projection(projection);

        // 定义比例尺，使用对数缩放
        const maleExtent = d3.extent(genderData, d => d.Males);
        const femaleExtent = d3.extent(genderData, d => d.Females);
        // 定义比例尺，使用对数缩放
        const xScale = d3.scaleLog()
            .domain([Math.max(1, maleExtent[0]), maleExtent[1]]) // 避免对数0值
            .range([0, gridSize - 1]);

        const yScale = d3.scaleLog()
            .domain([Math.max(1, femaleExtent[0]), femaleExtent[1]])
            .range([0, gridSize - 1]);

        const genderMap = new Map(genderData.map(d => [d.regionHZ, d])); // 转换为 Map 格式

        // 获取填充颜色
        const getColor = d => {
            const regionName = d.properties.name.replace(/市|县|区$/, ""); // 去掉最后一个字
            const regionData = genderMap.get(regionName);
            if (!regionData) return "white"; // 如果没有数据，填充灰色

            // 确保 Males 和 Females 至少为 1
            const males = Math.max(1, regionData.Males);
            const females = Math.max(1, regionData.Females);

            const x = Math.floor(xScale(males));
            const y = Math.floor(yScale(females));
            return colors[y * gridSize + x]; // 通过网格坐标查找颜色
        };

        // 绘制地图路径
        g.selectAll("path")
            .data(mapData.features)
            .join("path")
            .attr("class", "region-path")
            .attr("d", pathGenerator)
            .attr("stroke", "#000") // 边界线颜色
            .attr("stroke-width", 0.5) // 边界线宽度
            .attr("fill", d => getColor(d)) // 设置填充颜色
            .append("title") // 添加悬停提示
            .text(d => {
                const regionName = d.properties.name.replace(/市|县|区$/, "");
                const regionData = genderMap.get(regionName);
                return regionData
                    ? `${d.properties.name}\nMales: ${regionData.Males}\nFemales: ${regionData.Females}`
                    : `${d.properties.name}\nNo data`;
            });

        // 添加图例
        addLegend();
    };

    // 添加图例
    function addLegend() {
        const legendSize = 150; // 图例大小
        const legendSquareSize = legendSize / gridSize; // 单个颜色块大小

        svg.select(".legend").remove();

        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${svgW - legendSize - 40},${svgH - legendSize - 60})`);

        // 绘制颜色块
        const legendData = d3.cross(d3.range(gridSize), d3.range(gridSize));
        legend.selectAll("rect")
            .data(legendData)
            .join("rect")
            .attr("x", ([x]) => x * legendSquareSize)
            .attr("y", ([, y]) => (gridSize - 1 - y) * legendSquareSize)
            .attr("width", legendSquareSize)
            .attr("height", legendSquareSize)
            .attr("fill", ([x, y]) => colors[y * gridSize + x]);

        // 添加文字说明
        legend.append("text")
            .attr("x", -10)
            .attr("y", legendSize / 2)
            .attr("dy", "-0.5em")
            .attr("text-anchor", "end")
            .attr("font-size", "40px") // 设置字体大小
            .text("Females");

        legend.append("text")
            .attr("x", legendSize / 2)
            .attr("y", legendSize + 10)
            .attr("dy", "1em")
            .attr("text-anchor", "middle")
            .attr("font-size", "40px") // 设置字体大小
            .text("Males");

        // 添加对角线
        legend.append("line")
            .attr("x1", 0)
            .attr("x2", legendSize)
            .attr("y1", legendSize)
            .attr("y2", 0)
            .attr("stroke", "black")
            .attr("stroke-width", 1.5);
    };

    // 在组件挂载时加载地图数据
    onMount(() => {
        fetchMapData();
    });

    // 当 allPoetsIDs 变化时获取性别数据
    $: if (allPoetsIDs && allPoetsIDs.length > 0) {
        fetchGenderData();
    }
</script>

<style>
    .region-path:hover {
        fill: aquamarine;
    }

    svg {
        display: block;
        margin: auto;
    }
</style>

<div bind:clientWidth={width} bind:clientHeight={height}>
    <svg style="width: 100%;height: 100%" class="map"></svg>
</div>
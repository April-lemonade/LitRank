<script>
    import * as d3 from "d3";
    import {onMount} from "svelte";

    export let rankData;
    export let clear;
    export let width, height;
    export let missingWorkCount = -1;
    export let select;
    let statsArray;

    let svg;
    let xScale, yScale;

    $: if (rankData && missingWorkCount) {
        let countStats = {};
        rankData.forEach(item => {
            let unknownCount = item.workCount ? item.workCount.unknownCount : item.poetCount.unknownCount;
            countStats[unknownCount] = (countStats[unknownCount] || 0) + 1;
        });

        // 转换为可用的数组格式
        statsArray = Object.entries(countStats).map(([unknownCount, count]) => ({
            unknownCount: Number(unknownCount),
            count
        }));
        drawChart();
    }


    function drawChart() {
        const svg = d3.select("#svg");
        svg.selectAll("*").remove();
        const margin = {top: 20, right: 10, bottom: 40, left: 30}; // 设置边距
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        xScale = d3.scaleBand()
            .domain(statsArray.map((d) => d.unknownCount)) // x 轴的类别为 unknownCount
            .range([0, innerWidth])
            .padding(0.2);

        yScale = d3.scaleLinear()
            .domain([0, d3.max(statsArray, (d) => d.count)]) // y 轴范围为 [0, 最大值]
            .nice()
            .range([innerHeight, 0]);

        const chart = svg
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`); // 应用边距偏移

        // 添加 x 轴
        chart
            .append("g")
            .attr("transform", `translate(0,${innerHeight})`)
            .call(
                d3.axisBottom(xScale)
            )
            .selectAll("text")
            .style("text-anchor", "end");

        // 添加 y 轴
        chart
            .append("g")
            .call(
                d3.axisLeft(yScale)
                    .ticks(5) // y 轴显示 5 个刻度
            );

        // 添加 x 轴说明文字
        chart
            .append("text")
            .attr("x", innerWidth / 2) // 水平居中
            .attr("y", innerHeight + margin.bottom - 5) // 在横轴下方
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("Number of Missing Fields"); // 横轴说明文字

        // 添加 y 轴说明文字
        chart
            .append("text")
            .attr("x", -margin.left + 25) // 垂直居中
            .attr("y", 0) // y轴顶部
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text("Count"); // 纵轴说明文字

        // 绘制柱状图
        chart
            .selectAll("rect")
            .data(statsArray)
            .enter()
            .append("rect")
            .attr("x", (d) => xScale(d.unknownCount))
            .attr("y", (d) => yScale(d.count))
            .attr("width", xScale.bandwidth())
            .attr("height", (d) => innerHeight - yScale(d.count))
            .attr("fill", (d) => d.unknownCount === missingWorkCount || missingWorkCount === -1 ? 'steelblue' : 'grey')
            .on("click", (event, d) => {
                if (select) {
                    select(d.unknownCount)
                }
            });
    }
</script>

<div bind:clientWidth={width} bind:clientHeight={height} style="height: 15%">
    <svg bind:this={svg} width="100%" height="100%" id="svg"></svg>
</div>
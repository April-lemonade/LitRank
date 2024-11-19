<script>
    import {onMount} from 'svelte'
    import * as d3 from "d3";
    import {BARCHART_MARGIN_HORIZONTAL} from "../constants.js";
    import {BARCHART_MARGIN_VERTICAL} from "../constants.js";

    export let onBrushed; // 从父组件接收的函数


    export let width;
    export let height;
    export let BASE_URL;
    export let changing;
    let data = [];  // 用于存储从API获取的数据
    let xScale, yScale;
    let brush;
    let svgElement;

    onMount(async () => {
        const response = await fetch(`${BASE_URL}/workYear`);
        data = await response.json();

        const svg = d3.select("#workYear");

        // 清除已有的 brush 元素
        svg.select(".brush").remove();

        xScale = d3.scaleBand()
            .domain(data.map(d => d.StartYearRange))
            .range([BARCHART_MARGIN_HORIZONTAL, width - BARCHART_MARGIN_HORIZONTAL])
            .padding(0.1);

        yScale = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.Count)])
            .range([height - BARCHART_MARGIN_VERTICAL, 0]);

        brush = d3.brushX()
            .extent([[BARCHART_MARGIN_HORIZONTAL, 0], [width - BARCHART_MARGIN_HORIZONTAL, height - BARCHART_MARGIN_VERTICAL]])
            .on("end", brushed);

        // 创建新的 brush 元素
        const brushGroup = svg.append('g')
            .attr("class", "brush")
            .call(brush);

        // 设置默认全局范围
        brushGroup.call(brush.move, xScale.range());

        svg.selectAll(".x-axis")
            .data([null])
            .join("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0, ${height - BARCHART_MARGIN_VERTICAL})`)
            .call(d3.axisBottom(xScale));

        svg.selectAll(".x-axis text")  // 选择所有X轴的文本
            .style("text-anchor", "end") // 确保文本在旋转后对齐方式正确
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-45)"); // 旋转45度

        svg.selectAll(".y-axis")
            .data([null])
            .join("g")
            .attr("class", "y-axis")
            .attr("transform", `translate(${BARCHART_MARGIN_HORIZONTAL}, 0)`)
            .call(d3.axisLeft(yScale).ticks(4));
    });


    function brushed(event) {
        if (changing) return;

        // changing = true
        const selection = event.selection;
        if (selection) {
            // d3.select(".brush").call(brush.move, null);
            // 假设每个带的宽度已知，或者通过 xScale.step() 获取
            const bandwidth = xScale.bandwidth();
            const start = Math.floor((selection[0] - BARCHART_MARGIN_HORIZONTAL) / bandwidth);
            const end = Math.floor((selection[1] - BARCHART_MARGIN_HORIZONTAL) / bandwidth);

            // 可以直接使用 start 和 end 作为数据的索引
            console.log(`Brushed range from index ${start} to ${end}`);

            // 如果你需要确切的数据值，可以从 data 数组中获取
            if (start >= 0 && end < data.length + 1) {
                const brushedData = data.slice(start, end + 1);
                // console.log("Brushed Data:", brushedData);
                if (onBrushed) onBrushed({brushedData}); // 调用父组件传递的函数
            }
        }
    }
</script>

<div bind:clientWidth={width} bind:clientHeight={height} style="height: 100%">
    <svg bind:this={svgElement} width="100%" height="100%" id="workYear">
        {#each data as d}
            <rect x={xScale(d.StartYearRange)} y={yScale(d.Count)} width={xScale.bandwidth()}
                  height={height - BARCHART_MARGIN_VERTICAL - yScale(d.Count)} fill="{changing?'gray':'steelblue'}"/>
        {/each}
    </svg>
</div>

<style>
    .brush .selection {
        fill: steelblue; /* 刷选区域的填充色 */
        stroke: navy; /* 刷选区域的边框色 */
        stroke-width: 2; /* 边框宽度 */
        fill-opacity: 0.3; /* 填充的透明度 */
    }

    .brush .handle {
        fill: yellow; /* 手柄的颜色 */
        stroke: black; /* 手柄的边框颜色 */
    }

    .brush .overlay {
        pointer-events: all; /* 确保覆盖层可以捕捉到鼠标事件 */
    }

    svg {
        width: 100%;
        height: 100%;
    }
</style>
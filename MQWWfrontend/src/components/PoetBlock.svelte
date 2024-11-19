<script>
    import {COLORS} from "../constants.js";
    import * as d3 from "d3";
    import {onMount} from "svelte";

    export let width;  // 设置宽度
    export let height; // 设置高度
    export let poetPara = [];
    export let counts = [];
    export let poetAbsence;
    let data;
    let xScale, yScale;
    let linePath = null;
    let pixelWidth;
    let pixelHeight;
    let angleStep;
    let offsetAngle;
    let pieData;
    let pie;
    let arc;
    const color = d3.scaleOrdinal([
        "#FFF8DC", // 浅金色
        "#FFD700", // 标准金黄色
        "#FFC107", // 深金黄色
        "#FFB300", // 更深的橙黄色
        "#FFA000"  // 最深的金黄色
    ]);


    $: if (!poetAbsence) {
        data = Array.from({length: 14}, (_, i) => ({
            label: `Label${i + 1}`,  // 随意的标签名，可以替换
            value: 1
        }));
        // console.log(data)
        angleStep = 360 / data.length;
        offsetAngle = -angleStep / 2; // 起始角度偏移
    }

    $:if (poetAbsence && pixelWidth && pixelHeight) {
        // console.log(poetAbsence)
        // angleStep = 360 / poetAbsence.length;
        data = Object.entries(poetAbsence).map(([key, value]) => ({
            label: key,
            value: value !== 'unknown' ? 1 : 0
        }));
        angleStep = 360 / data.length;
        // console.log(data);
        const labels = data.map(d => d.label);

        xScale = d3.scalePoint()
            .domain(labels)
            .range([0, pixelWidth]);
        yScale = d3.scaleLinear()
            .domain([0, 1])
            .range([pixelHeight, 0]);

        const svg = d3.select(".lineChart");

        const lineGenerator = d3.line()
            .x(d => xScale(d.label))
            .y(d => yScale(d.value))
            .curve(d3.curveMonotoneX);

        linePath = lineGenerator(data);
        // console.log(linePath)

    }

    $:if (poetPara.length > 0 && counts.length > 0) {
        poetPara.forEach((item, index) => {
            if (index < COLORS.length) {
                item.color = COLORS[index][item.weight - 1];
            } else {
                item.color = COLORS[index % COLORS.length] + (item.weight * 100).toString();
            }
        });
        let total = counts.reduce((sum, current) => sum + current, 0);
        counts = counts.map(count => (count / total) * 100);
        pie = d3.pie().value(d => d);
        arc = d3.arc().innerRadius(0).outerRadius(50); // 设置饼图的半径
        pieData = pie(counts.filter(d => d > 0));
    }
</script>

<!--<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="height: {height}; width: {width};"-->
<!--     class="relative">-->
<!--    <div class="flex flex-row relative z-0" style="height: 100%; width: 100%;">-->
<!--        {#each poetPara as item, index}-->
<!--            <div class="{item.color}" style="width: {counts[index]}%"></div>-->
<!--        {/each}-->
<!--    </div>-->

<!--    &lt;!&ndash; 使用 linePath 来生成折线图路径 &ndash;&gt;-->
<!--    {#if linePath}-->
<!--        <div class="absolute left-0 top-0" style="height: 100%; width: 100%;">-->
<!--            <svg style="width: 100%; height: 100%;" class="lineChart">-->
<!--                <path d="{linePath}" fill="none" stroke="black" stroke-width="2"></path>-->
<!--            </svg>-->
<!--        </div>-->
<!--    {/if}-->
<!--</div>-->
<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="height: {height}; width: {width};"
     class="relative flex-none grow-0 shrink-0">
    {#if data }
        <svg width="100%" height="100%" viewBox="-10 -40 30 80">
            <!-- 花瓣 -->
            <g>
                {#each data as item, i}

                    <ellipse fill="{item.value !== 0?'#9dc0e3':'white'}" stroke="#5fa1cc"
                             cx="0" cy="-20" rx="6" ry="16"
                             transform="rotate({i * angleStep - angleStep/2})"
                    />

                {/each}
            </g>

            <!-- 花蕊线条 -->
            <!--            <g stroke="black" stroke-width="2">-->
            <!--                {#each data as item, i}-->
            <!--                    {#if item.value !== 0}-->
            <!--                        <line-->
            <!--                                x1="0"-->
            <!--                                y1="0"-->
            <!--                                x2="0"-->
            <!--                                y2="-20"-->
            <!--                                transform="rotate({i * angleStep})"-->
            <!--                        />-->
            <!--                    {/if}-->

            <!--                {/each}-->
            <!--            </g>-->

            <!-- 中心圆，放在花蕊之上 -->
            <g transform="scale(0.2)">
                {#each pieData as d, i}
                    <path d={arc(d)} fill={color(i)}></path>
                {/each}
            </g>
        </svg>
    {/if}
</div>
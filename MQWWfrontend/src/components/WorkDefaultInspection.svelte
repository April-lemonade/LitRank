<script>
    import * as d3 from "d3";
    import {onMount} from "svelte";

    export let width;  // 设置宽度
    export let height; // 设置高度
    export let pieData;

    export let selectWorkType;

    const color = d3.scaleOrdinal([
        "#A7C7E7", // 淡蓝色
        "#6AABD2", // 典雅蓝
        "#3A8FB7", // 中等蓝
        "#205493", // 深蓝色
        "#0F3557"  // 最深蓝
    ]);

    let pie = d3.pie().value(d => d.value);
    let arc = d3.arc().innerRadius(0).outerRadius(50);

    // 定义 tooltip
    let tooltip;
    onMount(() => {
        // Initialize Tooltip
        tooltip = document.createElement("div");
        tooltip.className = "tooltip";
        tooltip.style.position = "absolute";
        tooltip.style.background = "#f9f9f9";
        tooltip.style.padding = "5px";
        tooltip.style.border = "1px solid #ccc";
        tooltip.style.borderRadius = "4px";
        tooltip.style.pointerEvents = "none";
        tooltip.style.opacity = '0';
        tooltip.style.transition = "opacity 0.2s";
        document.body.appendChild(tooltip);

        // Add mouse events
        const paths = document.querySelectorAll(".pie-slice");
        paths.forEach((path, i) => {
            const data = pie(pieData)[i].data;
            path.addEventListener("mouseover", (event) => {
                tooltip.style.display = "block";
                tooltip.style.opacity = 1;
                tooltip.innerHTML = `${data.data.label}: ${data.data.value}`;
                tooltip.style.left = `${event.pageX + 10}px`;
                tooltip.style.top = `${event.pageY - 20}px`;
            });
            path.addEventListener("mouseout", () => {
                tooltip.style.display = "none";
                tooltip.style.opacity = 0;
            });
        });
    });

    function selectType(data) {
        if (selectWorkType) selectWorkType({data});
    }
</script>
<div bind:clientHeight={height} bind:clientWidth={width} style="width: {width};height:{height}"
     class="flex flex-col flex-none grow-0">
    <h3 class="text-lg">Work type Distribution</h3>
    <div class="flex flex-row">
        {#if pieData}
            <svg style="width: 100%;height: 100%">
                <g transform="translate(100, 80)">
                    {#each pieData as d, i}
                        <path class="pie-slice" d={arc(d)} fill={color(i)} on:click={()=>selectType(d)}></path>
                    {/each}
                </g>

            </svg>

            <!-- Tooltip -->
            <!--            <div class="tooltip"></div>-->

            <!-- 图例 -->
            <div class="legend flex flex-col gap-1 flex-none grow-0">
                {#each pieData as d, i}
                    <div class="legend-item" style="display: flex; align-items: center;">
                    <span class="legend-color"
                          style="display: inline-block; width: 10px; height: 10px; background-color: {color(i)}; margin-right: 5px;"></span>
                        <span>{d.data.label}</span>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

</div>

<style>
    .tooltip {
        font-size: 12px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
</style>
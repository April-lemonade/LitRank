<script>
    import '../output.css';
    import {BASE_URL, COLORS} from '../constants.js';
    import {onMount} from "svelte";

    export let workPara = [];
    export let width;
    export let height;
    export let counts = [];
    export let title;
    // let workAbsence;
    export let workAbsence

    export let workId;
    let weights;
    $:if (workAbsence) {
        workAbsence = Object.values(workAbsence)
    }
    $:if (workPara.length > 0 && counts.length > 0) {

        // console.log("countsraw", counts)
        let total = counts.reduce((sum, current) => sum + current, 0);
        counts = counts.map(count => (count / total) * 100);
        // console.log("counts", counts)

        // console.log(workId)
        // console.log(workPara)
        // let sortedPara = [...workPara].sort((a, b) => b.weight - a.weight);
        //
        // // 颜色映射
        // const colors = ['bg-stone-400', 'bg-stone-300', 'bg-stone-200', 'bg-stone-100'];
        //
        // // 创建权重到颜色的映射
        // const weightToColor = {};
        // let lastWeight = null;
        // let colorIndex = 0;  // 颜色索引初始化
        //
        // sortedPara.forEach(item => {
        //     if (item.weight !== lastWeight) {
        //         // 当遇到新的权重时，移动到下一个颜色
        //         lastWeight = item.weight;
        //         if (colorIndex < colors.length) {
        //             weightToColor[item.weight] = colors[colorIndex++];
        //         }
        //     } else {
        //         // 如果权重相同，使用上一个颜色
        //         weightToColor[item.weight] = colors[colorIndex - 1];
        //     }
        // });
        //
        // // 将颜色映射回原始数组
        // workPara.forEach(item => {
        //     item.color = weightToColor[item.weight];
        // });

        workPara.forEach((item, index) => {
            if (index < COLORS.length) {  // 确保不会超出colors数组的界限
                item.color = COLORS[index][item.weight - 1];  // 计算颜色代码
            } else {
                // 如果index超出colors数组长度，可以选择循环使用colors或者设定默认颜色
                item.color = COLORS[index % COLORS.length] + (item.weight * 100).toString();  // 循环使用colors数组
            }
        });
        // console.log(workPara)

        function selectBook(){

        }

    }
</script>

<div style="height: {height};width:{width}" class="relative" >
    <div class="flex flex-col" style="height: 100%;width:100%;">
        {#each workPara as item, index}
            <div class="{item.color}" style="height: {counts[index]}%"></div>
        {/each}
    </div>
    {#if title}
        <div class="text-sm absolute top-0 right-0 w-auto p-2 leading-4"
             style="z-index:99;white-space: break-spaces;height: 100%;overflow-wrap: break-word;writing-mode:vertical-rl">
            {@html title.split(/[:：﹕(,]/)[0]}
        </div>
    {/if}
    {#if workAbsence}
        <div class="absolute left-0 top-0 h-auto flex flex-col gap-0.5 justify-between pt-0.5 pb-0.5"
             style="width: 100%;height: 100%">
            {#each workAbsence as field}
                <div style="width: 50%;"
                     class="{field==='unknown'?'':'bg-black'} h-0.5 grow-0 shrink-0"></div>
            {/each}
        </div>

    {/if}
</div>

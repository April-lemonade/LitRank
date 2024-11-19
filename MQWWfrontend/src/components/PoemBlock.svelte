<script>
    import {COLORS} from "../constants.js";
    import {onMount} from "svelte";

    export let width;
    export let height;
    export let poemPara = [];
    export let counts = [];
    export let poemAbsence;
    let leftClipId = `leftHalf-${Math.random()}`;
    let rightClipId = `rightHalf-${Math.random()}`;


    let newPoemAbsence = {};
    let pixelWidth;
    let pixelHeight;
    let splitRatio = 0; // 左右比例，0.6 表示左边占60%，右边占40%

    let leftControlX; // 左侧控制点X
    let rightControlX; // 右侧控制点X
    const color = [
        ['#a7d084', '#86b564'], // 第一组：色相一致的浅绿色和深绿色
        ['#d6e9b3', '#b4d593']  // 第二组：色相一致的浅绿色和深绿色
    ];
    $:if (poemPara.length > 0 && poemAbsence) {
        poemPara.forEach((item, index) => {
            const groupIndex = index % color.length; // 确保 index 不越界
            item.color = color[groupIndex][0]; // 第一种浅绿色
        });
        // console.log(splitRatio)
        // console.log(poemPara)
        // console.log(poemAbsence)
        // console.log(counts)

        if (poemAbsence.GenreHZ === '詩') {
            newPoemAbsence = {
                Form: poemAbsence.Form,
                GenreHZ: poemAbsence.GenreHZ,
                Notes: poemAbsence.Notes,
                TitleHZ: poemAbsence.TitleHZ,
                changheshuxinpoetID: poemAbsence.changheshuxinpoetID,
                poetassubjectID: poemAbsence.poetassubjectID
            }
        }
        if (poemAbsence.GenreHZ === '詞' || poemAbsence.GenreHZ === '曲') {
            newPoemAbsence = {
                GenreHZ: poemAbsence.GenreHZ,
                Notes: poemAbsence.Notes,
                TitleHZ: poemAbsence.TitleHZ,
                changheshuxinpoetID: poemAbsence.changheshuxinpoetID,
                poetassubjectID: poemAbsence.poetassubjectID,
                TunePatternSubtitle: poemAbsence.TunePatternSubtitle
            }
        } else {
            newPoemAbsence = {
                GenreHZ: poemAbsence.GenreHZ,
                Notes: poemAbsence.Notes,
                TitleHZ: poemAbsence.TitleHZ,
                changheshuxinpoetID: poemAbsence.changheshuxinpoetID,
                poetassubjectID: poemAbsence.poetassubjectID,
                Form: '/'
            }
        }
    }

    $: if (counts.length > 0) {
        splitRatio = parseFloat((counts[0] / (counts[0] + counts[1])).toFixed(2));
        leftControlX = Math.round(200 - 100 * splitRatio);
        rightControlX = Math.round(200 + 100 * (1 - splitRatio));
        // console.log("Dynamic: SplitRatio:", splitRatio, "Left:", leftControlX, "Right:", rightControlX);
    }

    onMount(() => {
        setTimeout(() => {
            // 强制 Svelte 触发一次更新
            splitRatio = splitRatio;
        }, 50);
    });
</script>

<div bind:clientWidth={pixelWidth} bind:clientHeight={pixelHeight} style="height: {height}; width: {width};"
     class="relative flex-none grow-0 shrink-0">
    {#if splitRatio !== 0}
        <svg key={splitRatio} width="100%" height="100%" viewBox="0 0 10 600"
        >
            <defs>
                {#if splitRatio > 0}
                    <!-- 左半叶片剪切路径 -->
                    <clipPath id={leftClipId}>
                        <path d={`M200 50 C${leftControlX} 150 ${leftControlX} 450 200 550 L200 50 Z`}/>
                    </clipPath>
                    <!-- 右半叶片剪切路径 -->
                    <clipPath id={rightClipId}>
                        <path d={`M200 50 C${rightControlX} 150 ${rightControlX} 450 200 550 L200 50 Z`}/>
                    </clipPath>
                {/if}
            </defs>

            {#if splitRatio > 0}
                <rect x="0" y="0" width="400" height="600" fill={poemPara[0]?.color || "#a7d084"}
                      clip-path={`url(#${leftClipId})`}/>
                <rect x="0" y="0" width="400" height="600" fill={poemPara[1]?.color || "#d6e9b3"}
                      clip-path={`url(#${rightClipId})`}/>
            {/if}

            <!-- 主脉 -->
            <path d="M200 550 Q210 400 200 250 Q190 100 200 50"
                  fill="none"
                  stroke="#2c5f2d"
                  stroke-width="4"/>

            <!-- 分支脉络 -->
            {#if newPoemAbsence}
                <g stroke="#2c5f2d" fill="none">
                    <!-- 动态生成的分支 -->
                    {#each Object.entries(newPoemAbsence) as [key, value], i}
                        {#if value !== 'unknown'}
                            {#if i === 0}
                                <path d="M200 400 Q160 350 120 300" stroke-width="2"/>
                            {:else if i === 1}
                                <path d="M200 300 Q240 250 280 200" stroke-width="2"/>
                            {:else if i === 2}
                                <path d="M200 350 Q170 300 150 250" stroke-width="2"/>
                            {:else if i === 3}
                                <path d="M200 450 Q230 400 260 350" stroke-width="2"/>
                            {:else if i === 4}
                                <path d="M200 500 Q170 450 140 400" stroke-width="2"/>
                            {:else if i === 5}
                                <path d="M200 200 Q220 150 240 100" stroke-width="2"/>
                            {/if}
                        {/if}
                    {/each}
                </g>

            {/if}


            <!-- 叶子的轮廓 -->
            <path d="M200 50 C300 150 300 450 200 550 C100 450 100 150 200 50 Z"
                  fill="none"
                  stroke="#2c5f2d"
                  stroke-width="2"/>

            <!--            <text x="10" y="35" fill="black" font-size="50">-->
            <!--                {splitRatio.toFixed(2)}:{leftControlX.toFixed(2)}；{rightControlX.toFixed(2)}-->
            <!--            </text>-->

        </svg>
    {/if}

</div>
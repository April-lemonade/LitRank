<script>
    import WorkYearDistribution from "./components/WorkYearDistribution.svelte";
    import {BASE_URL} from './constants.js';
    import {onDestroy, onMount, tick} from "svelte";
    import './output.css';
    import WorkBook from "./components/WorkBook.svelte";
    import ColumnStats from "./components/ColumnStats.svelte";
    import PoetBlock from "./components/PoetBlock.svelte";
    import * as d3 from "d3";
    import WorkDefaultInspection from "./components/WorkDefaultInspection.svelte";
    import PoetDefaultInspection from "./components/PoetDefaultInspection.svelte";
    import SexMap from "./components/SexMap.svelte";
    import GenreTreeMap from "./components/GenreTreeMap.svelte";
    import PoetWork from "./components/PoetWork.svelte";
    import PoemBlock from "./components/PoemBlock.svelte";

    let width = window.innerWidth;
    let height = window.innerHeight;

    let works = [];
    let allWorkIDs = [];
    let allPoetsIDs = [];
    let allPoemsIDs = [];
    let previousWorkIDs = [];
    let previousPoetIDs = [];
    let previousPoemIDs = [];
    let selectedWorkPoet = [];
    let selectedWorkPoem = [];

    let rank = [];
    let poetRank = [];
    let poemRank = [];
    let selectedWork = [];
    let selectedPoet = [];
    let selectedPoem = []
    let workDetails = [];
    let poetDetails = [];
    let workColStats = [];
    let pie, arc, pieData;
    const color = d3.scaleOrdinal([
        "#A7C7E7", // 淡蓝色
        "#6AABD2", // 典雅蓝
        "#3A8FB7", // 中等蓝
        "#205493", // 深蓝色
        "#0F3557"  // 最深蓝
    ]);

    let changing = true
    let dialogTitle;

    function handleResize() {
        width = window.innerWidth;
        height = window.innerHeight;
    }

    let workPara = [
        {para: 'Inscription authors weight', weight: 1},
        {para: 'Preface authors weight', weight: 4},
        {para: 'Colophon authors weight', weight: 3},
        {para: 'Collected works weight', weight: 1}
    ];

    let poetPara = [
        {para: 'Works included weight', weight: 5},
        {para: 'Portrait mentions weight', weight: 1},
        {para: 'Portrait authored weight', weight: 3},
        {para: 'Response received weight', weight: 4},
        {para: 'Discussed weight', weight: 2}
    ];

    let poemPara = [
        {para: 'Work popularity weight', weight: 1},
        {para: 'Poet popularity weight', weight: 1}
    ];

    const workReferenceField = ['PubPlaceHZ', 'PubNameHZ', 'DateCycleHZ', 'DateEmperorHZ', 'DateDynastyHZ']
    const poetReferenceField = ['MainWorks', 'PresentdayEquivalent', 'LifeSpan', 'StartYear', 'EndYear', 'EthnicGroup']

    let currentWork = -1;
    let currentPoet = -1;
    let currentPoem = -1;

    let currentWorkDetail = {};
    let currentPoetDetail = {};
    let currentPoemDetail = {};

    function calculatePercentages(params, defaultPercentage) {
        currentWork = -1
        const totalWeight = params.reduce((sum, item) => sum + item.weight, 0);
        return params.map(item => ({
            ...item,
            percentage: totalWeight > 0
                ? (item.weight / totalWeight).toFixed(2)
                : defaultPercentage.toFixed(2)
        }));
    }


    $:{
        workPara = calculatePercentages(workPara, 0.25);
        poetPara = calculatePercentages(poetPara, 0.2);
        poemPara = calculatePercentages(poemPara, 0.2);
        importanceCal()
    }

    function importanceCal() {
        changing = true
        rank = []
        poetRank = []
        workDetails = []
        poetDetails = []
        let weights = workPara.flatMap(entry => entry.percentage)
        let poetWeights = poetPara.flatMap(entry => entry.percentage)
        let poemWeights = poemPara.flatMap(entry => entry.percentage)

        Promise.all([
            fetch(`${BASE_URL}/workImportance/${weights.join(',')}`)
                .then(response => response.json())  // 解析JSON格式的响应体
                .then(result => {
                    rank = result.data;  // 将结果赋值给 rank
                })
                .catch(error => {
                    console.error('Error fetching work importance data:', error);
                }),
            fetch(`${BASE_URL}/poetImportance/${poetWeights.join(',')}`)
                .then(response => response.json())  // 解析JSON格式的响应体
                .then(result => {
                    poetRank = result.data;  // 将结果赋值给 poetRank
                })
                .catch(error => {
                    console.error('Error fetching poet importance data:', error);
                })
        ])
            .then(() => {
                // 当 `workImportance` 和 `poetImportance` 都完成时，进行 `poemImportance` 的请求
                return fetch(`${BASE_URL}/poemImportance/${poemWeights.join(',')}`)
                    .then(response => response.json())
                    .then(result => {
                        poemRank = result.data;
                        // console.log("poemRank", poemRank);
                    })
                    .catch(error => {
                        console.error('Error fetching poem importance data:', error);
                    });
            })
            .then(() => {
                // 所有请求都完成后调用 `importanceSelected`
                importanceSelected();
            })
            .catch(error => {
                console.error('Error in fetching data:', error);
            });
    }

    async function importanceSelected() {
        changing = true;

        // 重置相关详情列表
        workDetails = [];
        poetDetails = [];

        // 异步获取和处理数据
        await processData();
        await tick();
        // 处理完毕，更新UI
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                changing = false;
            });
        });
    }

    async function processData() {
        const allWorkIDsInt = allWorkIDs.map(id => parseInt(id));
        const allPoetIDsInt = allPoetsIDs.map(id => parseInt(id));
        const allPoemIDsInt = allPoemsIDs.map(id => parseInt(id));

        selectedWork = rank.filter(item => allWorkIDsInt.includes(item.workID));
        selectedPoet = poetRank.filter(item => allPoetIDsInt.includes(item.poetID));
        selectedPoem = poemRank.filter(item => allPoemIDsInt.includes(item.poemID)).slice(0, 5000);

        calculatePieData();
    }

    function calculatePieData() {
        pie = d3.pie().value(d => d.value);
        arc = d3.arc().innerRadius(0).outerRadius(50);

        const worktypeCounts = selectedWork.reduce((acc, item) => {
            const worktype = item.workDetail.worktype;
            acc[worktype] = (acc[worktype] || 0) + 1;
            return acc;
        }, {});

        pieData = pie(Object.entries(worktypeCounts).map(([type, count]) => ({
            label: type,
            value: count
        })));

        // 更新 poet 详情
        poetDetails = selectedPoet.map(value => ({
            poetID: value.id,
            poetCount: value
        }));
    }


    window.addEventListener('resize', handleResize);

    onDestroy(() => {
        window.removeEventListener('resize', handleResize);
    })

    async function handleBrushed(data) {
        changing = true;
        currentWork = -1;
        currentWorkDetail = {};
        currentPoet = -1;
        currentPoetDetail = {};
        selectedWorkPoet = [];
        selectedWorkPoem = [];
        allWorkIDs = data.brushedData.flatMap(entry => entry.WorkIDs);
        // console.log("用户选择的年份范围变化", allWorkIDs)
        const getWorkColumnStatsResponse = await fetch(`${BASE_URL}/getWorkColumnStats/${allWorkIDs.toString()}`)
        workColStats = await getWorkColumnStatsResponse.json();

        // 使用 Promise.all 依次发起 `getSelectedPoets` 和 `getSelectedPoems` 请求
        const [selectedPoets, selectedPoems] = await Promise.all([
            fetch(`${BASE_URL}/getSelectedPoets/${allWorkIDs.toString()}`).then(response => response.json()),
            fetch(`${BASE_URL}/getSelectedPoems/${allWorkIDs.toString()}`).then(response => response.json())
        ]);

        // 将请求结果赋值
        allPoetsIDs = selectedPoets;
        allPoemsIDs = selectedPoems;
        previousPoetIDs = selectedPoets;
        previousPoemIDs = selectedPoems;

        // console.log("allPoemsIDs", allPoemsIDs);

        // 在所有数据处理完后调用 `importanceSelected`
        await importanceSelected();
    }

    function selectPoem(item) {
        if (currentWork === -1 || currentPoet === -1) return;
        console.log("selectPoem", item)
        changing = true;
        if (currentPoem === item.poemID) {
            currentPoem = -1;
            currentPoemDetail = {};
            // allPoemsIDs = previousPoemIDs;
            importanceSelected();
        } else {
            currentPoem = item.poemID;
            currentPoemDetail = item.poemDetail;
            if (currentPoemDetail.GenreHZ === '詩') {
                currentPoemDetail = {
                    Form: currentPoemDetail.Form,
                    GenreHZ: currentPoemDetail.GenreHZ,
                    Notes: currentPoemDetail.Notes,
                    TitleHZ: currentPoemDetail.TitleHZ,
                    changheshuxinpoetID: currentPoemDetail.changheshuxinpoetID,
                    poetassubjectID: currentPoemDetail.poetassubjectID
                }
            }
            if (currentPoemDetail.GenreHZ === '詞' || currentPoemDetail.GenreHZ === '曲') {
                currentPoemDetail = {
                    GenreHZ: currentPoemDetail.GenreHZ,
                    Notes: currentPoemDetail.Notes,
                    TitleHZ: currentPoemDetail.TitleHZ,
                    changheshuxinpoetID: currentPoemDetail.changheshuxinpoetID,
                    poetassubjectID: currentPoemDetail.poetassubjectID,
                    TunePatternSubtitle: currentPoemDetail.TunePatternSubtitle
                }
            } else {
                currentPoemDetail = {
                    GenreHZ: currentPoemDetail.GenreHZ,
                    Notes: currentPoemDetail.Notes,
                    TitleHZ: currentPoemDetail.TitleHZ,
                    changheshuxinpoetID: currentPoemDetail.changheshuxinpoetID,
                    poetassubjectID: currentPoemDetail.poetassubjectID,
                    Form: '/'
                }
            }
            currentPoemDetail = Object.fromEntries(
                Object.entries(currentPoemDetail).sort(([keyA, valueA], [keyB, valueB]) => {
                    const isUnknownA = valueA === "unknown" ? -1 : 0;
                    const isUnknownB = valueB === "unknown" ? -1 : 0;
                    return isUnknownA - isUnknownB;
                })
            );
            importanceSelected();
        }
    }

    function showLoading() {
        changing = true;
        console.log('Loading set to true');
    }

    function selectBook(item) {
        changing = true
        currentPoem = -1;
        currentPoet = -1;
        currentPoetDetail = {};
        currentPoemDetail = {};
        // console.log(item);

        if (currentWork === item.workID) {
            // document.getElementById("mymask").style.display = "flex"
            // changing = true
            console.log("test", currentWork, item.workID, changing);
            // changing = true
            currentWork = -1;
            currentPoet = -1;
            currentWorkDetail = {};
            selectedWorkPoet = [];
            allPoetsIDs = previousPoetIDs;
            allPoemsIDs = previousPoemIDs;
            importanceSelected();
        } else {
            currentWork = item.workID;
            currentWorkDetail = item.workDetail;

            // previousWorkIDs = allWorkIDs
            currentWorkDetail = Object.fromEntries(
                Object.entries(currentWorkDetail).sort(([keyA, valueA], [keyB, valueB]) => {
                    const isUnknownA = valueA === "unknown";
                    const isUnknownB = valueB === "unknown";

                    if (isUnknownA && isUnknownB) {
                        // 如果两个都是unknown，检查它们是否在列表中，并根据列表排序
                        const indexA = workReferenceField.indexOf(keyA);
                        const indexB = workReferenceField.indexOf(keyB);

                        // 判断是否在列表中
                        const isInListA = indexA !== -1;
                        const isInListB = indexB !== -1;

                        if (isInListA && isInListB) {
                            return indexA - indexB;
                        } else if (isInListA) {
                            return -1; // A在列表中，B不在，A排前
                        } else if (isInListB) {
                            return 1;  // B在列表中，A不在，B排前
                        }
                    } else if (isUnknownA && !isUnknownB) {
                        return -1; // A是unknown且不在列表中，B不是unknown，A排后（因为B可能在列表中）
                    } else if (!isUnknownA && isUnknownB) {
                        return 1;  // B是unknown且不在列表中，A不是unknown，B排后（因为A可能在列表中）
                    }

                    // 如果都不是unknown或不需要特别排序，保持原始顺序
                    return 0;
                })
            );
            // console.log('currentWorkDetail',currentWorkDetail);
            Promise.all([
                fetch(`${BASE_URL}/getSelectedPoets/${item.workID.toString()}`)
                    .then(response => response.json())
                    .then(selectedPoets => {
                        allPoetsIDs = selectedPoets;
                        selectedWorkPoet = allPoetsIDs;
                    }),
                fetch(`${BASE_URL}/getSelectedPoems/${item.workID.toString()}`).then(response => response.json()).then(selectedPoems => {
                    allPoemsIDs = selectedPoems;
                    selectedWorkPoem = allPoemsIDs;
                }),
            ]).then(() => {
                importanceSelected();
            });
            // console.log("currentSelectedPoets", selectedPoets);
            // console.log("currentSelectedPoems", selectedPoems);
        }
    }

    $:{
        if (changing) {
            console.log("loading")
        } else {
            console.log("loaded")
        }
    }

    function selectPoet(item) {
        if (currentWork === -1) return;
        changing = true
        if (currentPoet === item.poetID) {
            currentPoet = -1;
            currentPoem = -1;
            currentPoetDetail = {}
            allPoetsIDs = selectedWorkPoet;
            allPoemsIDs = selectedWorkPoem;
            importanceSelected();
        } else {
            currentPoem = -1;
            currentPoemDetail = {};
            currentPoet = item.poetID;
            currentPoetDetail = item.poetDetail;
            currentPoetDetail = Object.fromEntries(
                Object.entries(currentPoetDetail).sort(([keyA, valueA], [keyB, valueB]) => {
                    const isUnknownA = valueA === "unknown";
                    const isUnknownB = valueB === "unknown";

                    if (isUnknownA && isUnknownB) {
                        // 如果两个都是unknown，检查它们是否在列表中，并根据列表排序
                        const indexA = poetReferenceField.indexOf(keyA);
                        const indexB = poetReferenceField.indexOf(keyB);

                        // 判断是否在列表中
                        const isInListA = indexA !== -1;
                        const isInListB = indexB !== -1;

                        if (isInListA && isInListB) {
                            return indexA - indexB;
                        } else if (isInListA) {
                            return -1; // A在列表中，B不在，A排前
                        } else if (isInListB) {
                            return 1;  // B在列表中，A不在，B排前
                        }
                    } else if (isUnknownA && !isUnknownB) {
                        return -1; // A是unknown且不在列表中，B不是unknown，A排后（因为B可能在列表中）
                    } else if (!isUnknownA && isUnknownB) {
                        return 1;  // B是unknown且不在列表中，A不是unknown，B排后（因为A可能在列表中）
                    }

                    // 如果都不是unknown或不需要特别排序，保持原始顺序
                    return 0;
                })
            );
            if (currentWork !== -1) {
                fetch(`${BASE_URL}/getpoemsbyworkpoet/${currentWork}/${item.poetID}`)
                    .then(response => response.json())
                    .then(poems => {
                        console.log(poems)
                        allPoemsIDs = poems;
                        importanceSelected();
                    })
            }

        }
        // console.log(item)
    }

    let relatedContent;

    function selectField(label, type) {
        relatedContent = {}
        document.getElementById("my_modal_3").showModal();
        dialogTitle = label;
        if (type === 'work') {
            if (label === 'PubPlaceHZ') {
                let extractedData = selectedPoet
                    .filter(poet => poet.poetDetail.PresentdayEquivalent !== 'unknown') // 首先过滤掉 PresentdayEquivalent 为 'unknown' 的记录
                    .map(poet => {
                        return {
                            label: `${poet.poetID} - ${poet.poetDetail.NameHZ}`,
                            value: poet.poetDetail.PresentdayEquivalent
                        };
                    });

                // 计算每个 PresentdayEquivalent 的出现次数
                const frequency = extractedData.reduce((acc, curr) => {
                    acc[curr.value] = (acc[curr.value] || 0) + 1;
                    return acc;
                }, {});

                // 使用出现次数信息对 extractedData 进行排序
                extractedData.sort((a, b) => {
                    // 首先按频率降序排序
                    const freqComparison = frequency[b.value] - frequency[a.value];
                    if (freqComparison === 0) {
                        // 如果频率相同，可以按字母顺序排序或保持现有顺序
                        return a.value.localeCompare(b.value);
                    }
                    return freqComparison;
                });
                // console.log("extractedData", extractedData)
                relatedContent = {
                    title: 'The location of poets in this work',
                    content: extractedData
                }
                console.log(relatedContent)
            } else if (label === 'DateCycleHZ' || label === 'DateXF' || label === 'DateCycleHZ' || label === 'DateEmperorHZ') {
                if (currentWorkDetail.PubStartYear !== 0 || currentWorkDetail.PubEndYear !== 0) {
                    let years = [currentWorkDetail.PubStartYear, currentWorkDetail.PubEndYear]
                    years.filter(year => year !== 0)
                    fetch(`${BASE_URL}/getcyclebyyear/${years.toString()}`)
                        .then(response => response.json())
                        .then(yearData => {
                            console.log(yearData)
                            let extractedData = yearData
                                .filter(data => data.year !== 0)
                                .map((data, index) => {
                                    return {
                                        label: years[index],
                                        value: Object.values(data)
                                    }
                                })
                            // console.log(extractedData)
                            relatedContent = {
                                title: 'Reference according to known date',
                                content: extractedData
                            }
                            // console.log(relatedContent)
                        })
                }
            } else if (label === 'PubNameHZ') {
                fetch(`${BASE_URL}/getsimilarpoetworkpubname/${currentWork}`)
                    .then(response => response.json())
                    .then(workInfos => {
                        console.log(workInfos)
                        let extractedData = workInfos
                            .filter(data => data.PubNameHZ !== 'unknown')
                            .map((data, index) => {
                                return {
                                    label: data.WorkTitle,
                                    value: data.PubNameHZ
                                }
                            })
                        console.log(extractedData)
                        relatedContent = {
                            title: 'Works included same authors',
                            content: extractedData
                        }
                        console.log(relatedContent)
                    })
            }
        } else if (type === 'poet') {
            if (label === 'MainWorks') {
                fetch(`${BASE_URL}/getpoetworkrole/${currentPoet}`)
                    .then(response => response.json())
                    .then(roles => {
                        let extractedData = roles
                            .map((data, index) => {
                                return {
                                    label: data.IDTitle,
                                    value: data.role
                                }
                            })
                        console.log(extractedData)
                        relatedContent = {
                            title: 'Works included this author',
                            content: extractedData
                        }
                    })
            } else if (label === 'PresentdayEquivalent') {
                fetch(`${BASE_URL}/getsameworkpoetregion/${currentPoet}`)
                    .then(response => response.json())
                    .then(roles => {
                        let extractedData = roles
                            .map((data, index) => {
                                return {
                                    label: data.IDName,
                                    value: data.PresentdayEquivalent
                                }
                            })
                        console.log(extractedData)
                        relatedContent = {
                            title: "collaborated authors' regions",
                            content: extractedData
                        }
                    })
            } else if (label === 'StartYear' || label === 'EndYear') {
                fetch(`${BASE_URL}/getsameworkpoetyear/${currentPoet}`)
                    .then(response => response.json())
                    .then(years => {
                        let extractedData = years
                            .map((data, index) => {
                                return {
                                    label: data.IDName,
                                    value: `${data.StartYear}-${data.EndYear}`
                                }
                            })
                        relatedContent = {
                            title: "collaborated authors' Year",
                            content: extractedData
                        }
                    })
            } else if (label === 'EthnicGroup') {
                fetch(`${BASE_URL}/getsameworkpoetethnicgroup/${currentPoet}`)
                    .then(response => response.json())
                    .then(groups => {
                        let extractedData = groups
                            .filter(data => data.EthnicGroup !== 'unknown')
                            .map((data, index) => {
                                return {
                                    label: data.IDName,
                                    value: data.EthnicGroup
                                }
                            })
                        relatedContent = {
                            title: "collaborated authors' EthnicGroup",
                            content: extractedData
                        }
                    })
            }
        }
    }

    onMount(() => {
        // dialog = document.getElementById("my_modal_3");
        fetch(`${BASE_URL}/getAllWorkID`).then(response => {
            return response.json();
        }).then(workIDS => {
            const uniqueWorkIDs = new Set();
            const uniquePoetIDs = new Set();
            const uniquePoemIDs = new Set()
            workIDS.forEach(item => {
                uniqueWorkIDs.add(item.workID.toString()); // 添加 workID 到 Set 中去重
                item.poetIDs.split(',').forEach(poetID => uniquePoetIDs.add(poetID)); // 分割 poetIDs 字符串并去重
                item.poemIDs.split(',').forEach(poemID => uniquePoemIDs.add(poemID));
            });
            // console.log(workIDS);
            // workIDS = workIDS.map(String);
            // allWorkIDs = workIDS
            allWorkIDs = Array.from(uniqueWorkIDs);
            allPoetsIDs = Array.from(uniquePoetIDs);
            allPoemsIDs = Array.from(uniquePoemIDs);
            previousPoetIDs = Array.from(uniquePoetIDs);
            previousPoemIDs = Array.from(uniquePoemIDs);
            // console.log(allPoemsIDs)
            // importanceCal()
            fetch(`${BASE_URL}/getWorkColumnStats/${allWorkIDs.toString()}`).then(response => {
                return response.json();
            }).then(WorkColumnStats => {
                workColStats = WorkColumnStats
            })
        })
    })

    $: {
        if (changing) {
            document.getElementById("app").style.height = "100vh";
            document.getElementById("app").style.overflow = "hidden";
        } else {
            document.getElementById("app").style.overflow = "";
            document.getElementById("app").style.height = "";
        }
    }

</script>

<div bind:clientWidth={width} class="w-full flex flex-col flex-none grow-0 shrink-0 relative"
     style="max-width: 100vw">
    <div style="display: {changing?'flex':'none'};width:100vw;height:100vh;position:fixed;left:0;top:0;z-index:999;"
         class="bg-gray-300/50 mask" id="mymask">
        <span class="loading loading-spinner loading-lg absolute left-1/2" style="top: 50vh"></span>
    </div>
    <div class="navbar bg-base-300" style="width: 100vw">
        <button class="btn btn-ghost text-xl bar">MQWW</button>
    </div>
    <div class="flex flex-row gap-2 w-full p-4 flex-none" style="max-width: 100vw">
        <div class="basis-1/5 border border-slate-300 flex flex-col gap-4 p-4 rounded-md flex-none"
             style="max-width: 20%">
            <h1 class="text-xl">Parameter View</h1>
            <!--<label class="input input-bordered flex items-center gap-2">
                <input type="text" class="grow" placeholder="Search"/>
                <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 16 16"
                        fill="currentColor"
                        class="h-4 w-4 opacity-70">
                    <path
                            fill-rule="evenodd"
                            d="M9.965 11.026a5 5 0 1 1 1.06-1.06l2.755 2.754a.75.75 0 1 1-1.06 1.06l-2.755-2.754ZM10.5 7a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0Z"
                            clip-rule="evenodd"/>
                </svg>
            </label>-->
            <h2 class="text-lg">Time Period</h2>
            <div class="barSelect">
                <WorkYearDistribution width={'50%'} height={'70%'} {BASE_URL} onBrushed={handleBrushed} {changing}/>
            </div>
            <h2 class="text-lg">Popularity Parameters</h2>
            <h3>Work</h3>
            <div style="height: 15vh" class="w-full flex">
                <WorkBook {workPara} width={'30%'} height={'100%'} counts={[2,2,2,2]}></WorkBook>
            </div>

            {#each workPara as item, index}
                <div class="text-sm flex justify-between">
                    <div>{item.para} </div>
                    <div>{item.weight}</div>
                </div>
                <input type="range" min="0" max="4" bind:value={item.weight}
                       class="range range-xs  {changing?'range-secondary':'range-primary'}" step="1"
                       disabled={changing}/>
            {/each}
            <h3>Poet</h3>
            <div style="height: 10vh" class="w-full flex">
                <PoetBlock {poetPara} width={'100%'} height={'100%'} counts={[1,1,1,1,1]}></PoetBlock>
            </div>
            {#each poetPara as item, index}
                <div class="text-sm flex justify-between">
                    <div>{item.para} </div>
                    <div>{item.weight}</div>
                </div>
                <input type="range" min="0" max="5" bind:value={item.weight}
                       class="range range-xs {changing?'range-secondary':'range-primary'}" step="1"
                       disabled={changing}/>
            {/each}
            <h3>Poem</h3>
            <div style="height: 10vh" class="w-full flex">
                <PoemBlock {poemPara} width={'100%'} height={'100%'}
                           counts={[0.5,0.5]} poemAbsence="{[1,1,1,1,1,1]}"></PoemBlock>
            </div>
            {#each poemPara as item, index}
                <div class="text-sm flex justify-between">
                    <div>{item.para} </div>
                    <div>{item.weight}</div>
                </div>
                <input type="range" min="0" max="2" bind:value={item.weight}
                       class="range range-xs {changing?'range-secondary':'range-primary'}" step="1"
                       disabled={changing}/>
            {/each}
        </div>
        <div class="flex-none basis-3/5 max-w-[calc(60%)] border border-slate-300 p-4 rounded-md flex flex-col gap-4 grow-0"
             style="max-width: 60%">
            <h1 class="text-xl">Distribution View</h1>
            <h2 class="text-lg">Work</h2>
            <div class="flex flex-row gap-4">
                <ColumnStats class="shrink-0 grow-0 flex-none" width={'100%'} height={'100%'} {BASE_URL}
                             {workColStats}></ColumnStats>
                <div class="flex flex-row gap-4 overflow-x-auto" style="min-width: 90%;max-width: 90%">
                    {#if selectedWork}
                        {#each selectedWork as item,index}
                            <div class="shrink-0 flex flex-col {currentWork!==item.workID&&currentWork!==-1?'grayscale':''}"
                                 style="height: 20vh;width: 6vw"
                                 on:click={() => selectBook(item)}>
                                <WorkBook class="h-max" {workPara} width={'100%'} height={'100%'}
                                          counts={[
                  parseFloat(item.workCount.ticiCalc) || 0,
                  parseFloat(item.workCount.xuCalc) || 0,
                  parseFloat(item.workCount.baCalc) || 0,
                  parseFloat(item.workCount.includedCalc) || 0
              ]} title="{item.workDetail?item.workDetail.TitleHZ:'unknown'}"
                                          workId="{parseInt(item.workID)}"
                                          workAbsence="{item.workDetail}"></WorkBook>
                                <!--                                <div class="shrink-0">{item.workID}</div>-->
                            </div>

                        {/each}
                    {/if}
                </div>
            </div>
            <h2 class="text-lg">Poet</h2>
            <div class="flex flex-row gap-4 flex-wrap overflow-y-auto flex-none grow-0 shrink-0 w-full justify-center"
                 style="max-height: 50vh">
                {#each selectedPoet as item}
                    <div class="flex flex-none shrink-0 grow-0 {currentPoet!==item.poetID&&currentPoet!==-1?'grayscale':''}"
                         style="width: 6vw;height: 10vh" on:click={() => selectPoet(item)}>
                        <PoetBlock {poetPara} width={'100%'} height={'100%'}
                                   counts={[parseFloat(item.poetCount.participateCalc),parseFloat(item.poetCount.writeXZCalc),
                                            parseFloat(item.poetCount.inXZCalc),parseFloat(item.poetCount.bediscussedCalc),
                                            parseFloat(item.poetCount.changheCalc)]}
                                   poetAbsence="{item.poetDetail}"
                                   class="flex-none grow-0 shrink-0 ">
                        </PoetBlock>
                    </div>
                    <!--                    <div>{item.poetID}</div>-->
                {/each}
            </div>
            <h2 class="text-lg">Poem</h2>
            <div class="flex flex-row gap-4 flex-wrap overflow-y-auto flex-none grow-0 shrink-0 w-full"
                 style="max-height: 70vh">
                {#if (selectedPoem.length) === 0}
                    <div>No Records</div>
                {:else }
                    {#each selectedPoem as item}
                        <!--<div class="flex flex-none shrink-0 grow-0" style="width: 10vw;height: 10vh"
                             on:click={() => selectPoet(item)}>
                            <PoetBlock {poetPara} width={'100%'} height={'100%'}
                                       counts={[parseFloat(item.poetCount.participateCalc),parseFloat(item.poetCount.writeXZCalc),parseFloat(item.poetCount.inXZCalc),parseFloat(item.poetCount.bediscussedCalc),parseFloat(item.poetCount.changheCalc)]}
                                       poetAbsence="{item.poetDetail}"
                                       class="flex-none grow-0 shrink-0 {currentPoet!==item.poetID&&currentPoet!==-1?'grayscale':''}">
                            </PoetBlock>
                        </div>-->
                        <div class="flex flex-none shrink-0 grow-0 justify-center {currentPoem!==item.poemID&&currentPoem!==-1?'grayscale':''}"
                             style="width: 5vw;height: 10vh" on:click={() => selectPoem(item)}>
                            <PoemBlock {poemPara} width={'100%'} height={'100%'}
                                       counts={[parseFloat(item.poemCount.workImportance),parseFloat(item.poemCount.poetImportance)]}
                                       poemAbsence="{item.poemDetail}"></PoemBlock>
                        </div>
                        <!--                        <div>{item.poemID}</div>-->
                    {/each}
                {/if}
            </div>
        </div>
        <div class="basis-1/5 border border-slate-300 p-4 rounded-md flex flex-none flex-col grow-0 shrink-0 gap-4"
             style="max-width: 20%">
            <h1 class="text-xl">Inspection View</h1>

            <div class="join join-vertical w-full">
                <div class="collapse collapse-arrow join-item border-base-300 border">
                    <input type="checkbox" name="my-accordion-4" checked="{currentWork===-1}"/>
                    <div class="collapse-title text-xl font-medium">Work</div>
                    <div class="collapse-content">
                        {#if currentWork === -1}
                            <div style="min-height: 20vh">
                                <WorkDefaultInspection width={'100%'} height={'100%'} {pieData}></WorkDefaultInspection>
                            </div>
                        {:else }
                            <div class="flex flex-col gap-2" style="min-height: 20vh">
                                {#each Object.entries(currentWorkDetail) as [label, value]}
                                    {#if value === 'unknown' && workReferenceField.includes(label)}
                                        <button class="btn"
                                                on:click={()=>selectField(label,'work')}>{label}：{value}</button>
                                    {:else}
                                        <div>{label}：{value}</div>
                                    {/if}
                                {/each}
                                <dialog id="my_modal_3" class="modal">
                                    <div class="modal-box">
                                        <form method="dialog">
                                            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">
                                                ✕
                                            </button>
                                        </form>
                                        <h3 class="text-lg font-bold">{dialogTitle}</h3>
                                        {#if relatedContent}
                                            <div>{relatedContent.title}</div>
                                            {#each relatedContent.content as item}
                                                <p class="py-4">{item.label} : {item.value}</p>
                                            {/each}
                                        {/if}
                                    </div>
                                    <form method="dialog" class="modal-backdrop">
                                        <button>close</button>
                                    </form>
                                </dialog>
                            </div>
                        {/if}
                    </div>
                </div>
                <div class="collapse collapse-arrow join-item border-base-300 border">
                    <input type="checkbox" name="my-accordion-4" checked="{currentPoet !== -1 && currentPoem === -1}"/>
                    <div class="collapse-title text-xl font-medium">Poet</div>
                    <div class="collapse-content">
                        {#if currentWork !== -1 && currentPoet === -1}
                            <div style="min-height: 20vh">
                                <PoetDefaultInspection width={'100%'} height={'100%'}
                                                       workID={currentWork}></PoetDefaultInspection>
                            </div>
                        {/if}
                        {#if currentWork === -1 && currentPoet === -1}
                            <div style="min-height: 20vh">
                                <SexMap width={'100%'} height={'100%'} {allPoetsIDs}></SexMap>
                            </div>
                        {/if}
                        {#if currentPoet !== -1}
                            <div class="flex flex-col gap-2">
                                {#each Object.entries(currentPoetDetail) as [label, value]}
                                    {#if value === 'unknown' && poetReferenceField.includes(label)}
                                        <button class="btn"
                                                on:click={()=>selectField(label,'poet')}>{label}：{value}</button>
                                    {:else}
                                        <div>{label}：{value}</div>
                                    {/if}
                                {/each}
                                <div style="min-height: 20vh">
                                    <PoetWork width={'100%'} height={'100%'} poetID={currentPoet}></PoetWork>
                                </div>
                            </div>
                        {/if}

                    </div>
                </div>
                <div class="collapse collapse-arrow join-item border-base-300 border">
                    <input type="checkbox" name="my-accordion-4" checked="{currentPoem !== -1}"/>
                    <div class="collapse-title text-xl font-medium">Poem</div>
                    <div class="collapse-content">
                        {#if currentPoem === -1}
                            <div style="min-height: 20vh;max-height: 50vh">
                                <GenreTreeMap width={'100%'} height={'100%'}
                                              {allPoemsIDs}></GenreTreeMap>
                            </div>
                        {:else}
                            {#each Object.entries(currentPoemDetail) as [label, value]}
                                <div>{label}：{value}</div>
                            {/each}
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>

    .barSelect {
        width: 100%;
        height: 20vh;
    }

    .p-4 {
        padding: 1rem;
    }

    .range-secondary {
        --range-shdw: gray;
    }

    body {
        height: 100vh;
        /*overflow-y: scroll;*/
    }

    .modal {
        top: 10%;
        left: 55%;
        height: max-content;
        max-width: 27%;
        /*max-height: 50%;*/
        display: block !important;
        justify-items: start !important;
        /*overflow: hidden;*/
    }

    .modal::backdrop {
        /*background-color: transparent !important;*/
        animation: modal-pop 0.2s ease-out;
    }

    .modal-box {
        max-height: 80vh;
        overflow: scroll;
    }

    .modal-backdrop {
        position: fixed;
        width: 100vw;
        height: 100vh;
        top: 0;
        left: 0;
    }
</style>

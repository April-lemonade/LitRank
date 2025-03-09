# Popularity Calculation

## Poet

* 作品分布的集的数量
* 被写年谱/略传/传的次数
* 被诗话/词话/案语讨论的次数

## Work

作者的weight * 作者的popularity

### **作者的weight计算方式：**

1. **初始角色权重**

   * 主文本作者 0.6
     * 主要作者/作者/其他作者
   * 副文本作者 0.3
     * 题辞/序作者/跋作者/附记作者/凡例作者/墓志铭作者/挽词作者/传记作者/像赞作者/年谱作者

   * 编辑作者 0.1
     * 编辑/校阅/校注者

2. **赋予每位poet角色权重**
   根据作者担任的角色，分配相应的权重。如果一位作者担任多个角色，需要将各个角色的权重相加。

3. **计算poet的加权重要性**

   对于每位poet，将其基本重要性与其角色权重相乘，以得到加权重要性。

4. **聚合集的总重要性**

   将所有poet的加权重要性相加，得到集的总重要性。

### **示例**

- **Poet A**
  - role: 主文本作者, 编辑
  - popularity: 0.8
- **Poet B**
  - role: 副文本作者
  - popularity: 0.5
- **Poet C**
  - role: 编辑
  - popularity: 0.6

**角色权重分配：**

- **Poet A**: 主文本作者 (0.6) + 编辑 (0.1) = 0.7
- **Poet B**: 副文本作者 = 0.3
- **Poet C**: 编辑 = 0.1

**计算加权重要性：**

- **Poet  A**: 0.8 * 0.7 = 0.56 
- **Poet B**: 0.5 * 0.3 = 0.15 
- **Poet C**: 0.6* 0.1 = 0.06 

**文集的总重要性：**

总重要性 = 0.56 + 0.15 + 0.06 = 0.77 

Dear Hongxin,

 

Happy Lunar New Year and congratulations to you and your team for getting your paper accepted for publication. I read it with great interest. Here are some of my questions:

 

The LitRank interactive tool is not available to public users. Does your research group intend to make it accessible?

The explanation of “Popularity Calculation” is technical and not easy to follow.

How do you arrive at the top ranking collections? How did LitRank select the top 5 collections and the top 5 poets? What criteria are used? The case of the top 5 collections is especially puzzling—they consist of different categories of collections: 別集, 總集, and 合刻. In what way are they comparable?

In endnote 25, the full citation should be: [25] Q. Huang, “Writing from within a Women’s Community: Gu Taiqing (1799-1877) and Her Poetry,” M.A. Thesis, McGill University, 2004. Qiaole Huang was my MA student.

The URL for MQWW should be included in the paper.

 

I hope your team can refine the method and the tool of LitRank and make it available to scholars, students, and researchers.

 

Best wishes for 2025,

帮我回邮件，感谢她提到的建议，我对文章已经进行了相应的修改。

1. 在文中datasets description部分加上了数据集的网站链接。修改引用：Q. Huang, “Writing from within a Women’s Community: Gu Taiqing (1799-1877) and Her Poetry,” Master’s thesis, McGill University, 2004.

2. popularity表述不明，改为更合适的Literary Impact。我们想通过计量分析的方法来评估作者和文集在文学史上的重要性和影响力。在与一位中文系教授的访谈中，我们制定了具体的计算规则，作者的影响力（impact）主要由以下几个因素决定：一是作者在不同文集中的出现频率，二是该作者在诗话、词话等文学评论中的讨论次数，三是作者在年谱、略传、传记中的出现频率。而文集的影响力则由其作者的影响力和作者在文集中的角色决定。用户可以根据自己的分析需求，调整这些因素的权重，以便更加符合他们的研究目标。例如，如果用户希望更侧重于分析作者在文学评论中的学术影响力，他们可以增加“文学评论中被讨论的次数”的权重，减少其他因素的比重。后面的排名是根据这个impact得出的。

3. 我们此前确实忽略了文集的类型，不同类型的文集不应该一起排名。所以我们新加入了对于文集类型的筛选，由此可以得到不同类型的文集的排名。

4. 原型系统已经部署到我的个人服务器，访问地址为：https://litrank.april-fu.com/ 。由于服务器配置不高，访问速度收到了影响，但是可以进行基本的体验。

   受到本次投稿的时间限制，我需要在2.6之前提交终稿，这个项目还有很多可以完善的地方，原型还可以再迭代优化，impact的计算规则也还可以和更多的领域专家进行商讨优化。但是这是我们对于可视分析系统以及计量分析在文学领域的一次尝试。修改后的文件已经上传附件。
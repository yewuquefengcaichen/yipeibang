const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const quickQuestions = [
  "平时我同学有夜间出汗，怎么办？帮我分析一下",
  "明天内分泌科复诊，空腹血糖8.2，最近夜里出汗，要带什么？",
  "糖化血红蛋白7.4%和尿酸430是什么意思？",
  "帮我把二甲双胍和血糖记录整理成问医生的问题",
  "下次复诊前一天晚上8点提醒我，并同步给家属",
  "我胸痛、呼吸困难、脸色发白，现在怎么办？"
];

const themes = [
  {
    id: "clinical",
    name: "奶白医疗",
    desc: "清爽、可信、适合默认演示",
    swatches: ["#f7f9fc", "#0f9f9a", "#b8793a"]
  },
  {
    id: "jade",
    name: "青瓷陪诊",
    desc: "浅青和玉色，柔和亲近",
    swatches: ["#f3fbf8", "#14b8a6", "#2f7d64"]
  },
  {
    id: "sunrise",
    name: "暖金晨光",
    desc: "更温暖，适合复诊清单",
    swatches: ["#fff8f0", "#d28a3c", "#2563eb"]
  },
  {
    id: "ocean",
    name: "海盐蓝",
    desc: "医疗蓝和浅雾背景",
    swatches: ["#f2f8ff", "#2563eb", "#06b6d4"]
  },
  {
    id: "graphite",
    name: "石墨专业",
    desc: "低调、克制、像工作台",
    swatches: ["#f4f5f7", "#334155", "#0f766e"]
  },
  {
    id: "midnight",
    name: "夜间诊室",
    desc: "深色模式，适合投影演示",
    swatches: ["#111827", "#7aa2ff", "#2dd4bf"]
  }
];

const demoRoutes = [
  {
    id: "demo-night-sweat",
    title: "夜间出汗分层",
    prompt: "平时我同学有夜间出汗，怎么办？帮我分析一下",
    expectedIntent: "symptom_triage + memory_update",
    writes: ["症状记录", "风险关注记忆"],
    actions: ["识别红旗信号", "生成追问", "给出就医边界"],
    image: "./assets/medical/clinic-consult.jpg"
  },
  {
    id: "demo-glucose-followup",
    title: "空腹血糖8.2复诊",
    prompt: "明天内分泌科复诊，空腹血糖8.2，最近夜里出汗，要带什么？",
    expectedIntent: "prepare_visit + record_glucose + reminder_create",
    writes: ["血糖记录", "复诊任务", "主动提醒"],
    actions: ["复诊材料清单", "问医生的问题", "家属同步提示"],
    image: "./assets/medical/diabetes-care.jpg"
  },
  {
    id: "demo-bp-followup",
    title: "血压150/96随访",
    prompt: "最近三天血压150/96，头有点胀，帮我记录并提醒复查",
    expectedIntent: "record_vital + followup_reminder",
    writes: ["血压记录", "复查提醒"],
    actions: ["记录风险色", "生成复查清单", "提醒完成后回填"],
    image: "./assets/medical/blood-pressure.jpg"
  }
];

const medicalImages = {
  consult: "./assets/medical/clinic-consult.jpg",
  doctor: "./assets/medical/doctor-tablet.jpg",
  pressure: "./assets/medical/blood-pressure.jpg",
  diabetes: "./assets/medical/diabetes-care.jpg",
  report: "./assets/medical/lab-report.jpg",
  medicine: "./assets/medical/medicine-bottle.jpg",
  hospital: "./assets/medical/hospital-corridor.jpg",
  lifestyle: "./assets/medical/healthy-life.jpg",
  elder: "./assets/medical/elder-care.jpg",
  team: "./assets/medical/medical-team.jpg",
  xray: "./assets/medical/xray-check.jpg",
  family: "./assets/medical/family-care.jpg"
};

const caseLibrary = [
  { id: "case-night-sweat", title: "夜间出汗与低血糖风险", patient: "20岁学生，夜间盗汗反复出现", scenario: "症状分层、危险信号、就医问题", image: medicalImages.consult, prompt: "平时我同学有夜间出汗，怎么办？帮我分析一下", tags: ["症状", "内分泌", "安全"] },
  { id: "case-diabetes-follow", title: "糖尿病复诊准备", patient: "68岁，2型糖尿病，空腹血糖8.2", scenario: "复诊材料、用药清单、血糖记录", image: medicalImages.diabetes, prompt: "明天内分泌科复诊，空腹血糖8.2，最近夜里出汗，要带什么？", tags: ["糖尿病", "复诊", "记忆"] },
  { id: "case-hypertension", title: "高血压三日随访", patient: "55岁，血压150/96，头胀", scenario: "趋势记录、复查提醒、风险判断", image: medicalImages.pressure, prompt: "最近三天血压150/96，头有点胀，帮我记录并提醒复查", tags: ["血压", "随访", "提醒"] },
  { id: "case-chest-pain", title: "胸痛急症识别", patient: "62岁，胸痛伴呼吸困难", scenario: "急症安全拦截、120提醒", image: medicalImages.hospital, prompt: "我胸痛、呼吸困难、脸色发白，现在怎么办？", tags: ["急症", "安全", "120"] },
  { id: "case-report", title: "糖化血红蛋白与尿酸解读", patient: "体检报告：HbA1c 7.4%，尿酸430", scenario: "指标解释、复诊问题生成", image: medicalImages.report, prompt: "糖化血红蛋白7.4%和尿酸430是什么意思？", tags: ["报告", "指标", "问诊"] },
  { id: "case-medication", title: "二甲双胍用药沟通", patient: "长期用药，担心漏服和胃肠反应", scenario: "用药清单、医生沟通问题", image: medicalImages.medicine, prompt: "帮我把二甲双胍和血糖记录整理成问医生的问题", tags: ["用药", "糖尿病", "清单"] },
  { id: "case-child-fever", title: "儿童反复发热就诊准备", patient: "6岁，发热两天，最高38.8", scenario: "体温曲线、用药记录、急诊信号", image: medicalImages.family, prompt: "孩子反复发热两天，最高38.8，去医院前要准备什么？", tags: ["儿童", "发热", "家属"] },
  { id: "case-thyroid", title: "甲状腺术后复查", patient: "45岁，术后两周复查", scenario: "病理报告、伤口恢复、复查项目", image: medicalImages.xray, prompt: "甲状腺术后两周复查，需要带哪些资料，报告要问什么？", tags: ["术后", "复查", "报告"] },
  { id: "case-insomnia", title: "睡眠质量下降", patient: "长期熬夜，入睡困难，白天乏力", scenario: "生活方式、记录睡眠、就医边界", image: medicalImages.lifestyle, prompt: "最近睡眠质量很差，白天乏力，应该怎么记录和调整？", tags: ["睡眠", "生活方式", "记录"] },
  { id: "case-nausea", title: "恶心症状初步分层", patient: "出现恶心，伴随情况未明确", scenario: "危险信号、饮食用药回顾、就医建议", image: medicalImages.doctor, prompt: "我出现恶心症状，帮我分析需要注意什么", tags: ["恶心", "症状", "分层"] },
  { id: "case-family-sync", title: "陪诊家属同步", patient: "家属陪诊，担心遗漏医生交代", scenario: "摘要生成、家属同步、提醒", image: medicalImages.elder, prompt: "下次复诊前一天晚上8点提醒我，并同步给家属", tags: ["家属", "提醒", "摘要"] },
  { id: "case-physical", title: "体检异常复查计划", patient: "体检多项指标异常，暂未就医", scenario: "异常指标归类、复查优先级", image: medicalImages.team, prompt: "体检报告有几项异常，帮我整理复查优先级和问医生的问题", tags: ["体检", "指标", "复查"] }
];

const knowledgeLayers = [
  {
    id: "symptoms",
    name: "症状知识库",
    icon: "stethoscope",
    image: medicalImages.consult,
    items: [
      ["夜间出汗", "记录发生时间、是否浸湿衣物、是否伴随心慌手抖、低热、体重下降；糖尿病患者应关注低血糖可能。"],
      ["恶心", "先判断是否伴随胸痛、剧烈腹痛、呕血、意识改变；再回顾饮食、药物、血糖波动和感染可能。"],
      ["头晕", "记录血压、血糖、发作姿势和持续时间；伴说话不清、肢体无力时应急诊。"],
      ["发热", "记录体温曲线、最高温、退热药使用时间；儿童和老人更要关注精神状态和饮水尿量。"],
      ["胸闷胸痛", "胸痛伴呼吸困难、出汗、脸色发白、压榨感时优先拨打120，不做线上等待。"],
      ["乏力", "结合睡眠、饮食、近期感染、贫血、甲状腺、血糖等线索整理给医生。"],
      ["咳嗽", "记录干咳或咳痰、痰色、发热、胸痛、接触史；慢病患者关注氧饱和度。"],
      ["腹痛", "关注部位、性质、持续时间、呕吐腹泻、黑便血便；剧烈或持续加重应就医。"],
      ["心慌", "记录心率、持续时间、诱因、是否胸痛气短；反复发作建议做心电图评估。"],
      ["水肿", "观察脚踝、眼睑、体重变化，结合肾功能、心功能、用药情况复查。"],
      ["视物模糊", "糖尿病、高血压患者需关注眼底和血糖血压控制情况。"],
      ["体重下降", "非主动减重且持续下降，应记录饮食、发热、盗汗、胃肠症状并尽快就诊。"]
    ]
  },
  {
    id: "diseases",
    name: "疾病知识库",
    icon: "heart-pulse",
    image: medicalImages.hospital,
    items: [
      ["2型糖尿病", "复诊重点包括血糖记录、糖化血红蛋白、低血糖经历、饮食运动和用药依从性。"],
      ["高血压", "家庭血压要固定时间、坐位安静测量，连续记录比单次测量更有参考价值。"],
      ["冠心病风险", "胸痛、气短、出冷汗属于高风险组合，应优先急救而不是线上咨询。"],
      ["甲状腺疾病", "常见复查包括甲功、超声、用药情况和术后症状变化。"],
      ["痛风与高尿酸", "尿酸升高需结合关节症状、肾功能、饮食和用药决定处理方案。"],
      ["慢性肾病风险", "关注肌酐、尿蛋白、血压、水肿和用药安全。"],
      ["慢阻肺", "记录咳嗽咳痰、活动后气促、氧饱和度和急性加重次数。"],
      ["贫血", "结合血红蛋白、铁蛋白、月经/消化道出血线索进一步评估。"],
      ["胃食管反流", "反酸烧心、夜间咳嗽、进食关系和用药情况都应记录。"],
      ["睡眠障碍", "记录入睡时间、夜醒次数、咖啡因、屏幕使用和白天困倦。"],
      ["儿童上呼吸道感染", "关注精神状态、呼吸、饮水尿量和持续高热。"],
      ["术后复查", "带出院小结、手术记录、病理报告、用药清单和恢复症状记录。"]
    ]
  },
  {
    id: "indicators",
    name: "体检指标知识库",
    icon: "file-heart",
    image: medicalImages.report,
    items: [
      ["空腹血糖", "反映空腹状态血糖水平，目标值需结合年龄、病程、并发症由医生确定。"],
      ["糖化血红蛋白", "反映近2-3个月平均血糖控制，适合和日常血糖记录一起看。"],
      ["尿酸", "升高可能与饮食、代谢、肾功能和药物有关，不能只凭一次结果判断。"],
      ["血压", "家庭血压应记录日期、时间、左右臂、心率和当时症状。"],
      ["低密度脂蛋白", "心血管风险越高，医生设定的控制目标通常越严格。"],
      ["肌酐/eGFR", "用于评估肾功能，用药前后和慢病随访中很重要。"],
      ["尿蛋白", "提示肾脏损伤风险，糖尿病高血压患者尤其需要关注。"],
      ["血红蛋白", "偏低可提示贫血，需要结合MCV、铁蛋白、出血线索。"],
      ["白细胞", "升高或降低都需结合发热、感染症状、用药和复查趋势。"],
      ["CRP", "炎症指标，不能单独定位病因，需要结合症状和体征。"],
      ["甲状腺功能", "TSH、FT3、FT4需要结合症状、用药和妊娠等情况解释。"],
      ["肝功能", "ALT/AST升高要回顾饮酒、脂肪肝、药物和病毒性肝炎筛查。"]
    ]
  },
  {
    id: "medication",
    name: "用药提醒知识库",
    icon: "pill",
    image: medicalImages.medicine,
    items: [
      ["二甲双胍", "常见沟通点包括胃肠反应、肾功能、漏服处理和是否需要随餐服用。"],
      ["降压药", "不要自行停药或加量，记录血压趋势和不适后让医生评估。"],
      ["他汀类药物", "关注肌肉酸痛、肝功能、血脂目标和是否长期服用。"],
      ["阿司匹林", "需关注出血风险、胃部不适和是否有明确适应证。"],
      ["退热药", "儿童退热药需严格按说明和医生建议，不混用不超量。"],
      ["抗生素", "不建议自行购买或随意停用，需明确是否细菌感染和疗程。"],
      ["胰岛素", "记录剂量、注射时间、血糖和低血糖事件，复诊时一起给医生看。"],
      ["甲状腺素", "常需固定时间服用，并关注与钙铁制剂间隔。"],
      ["止痛药", "长期或频繁使用应关注胃肠、肾功能和掩盖症状风险。"],
      ["胃药", "明确是短期缓解还是长期治疗，持续症状应进一步评估。"],
      ["漏服记录", "记录漏服药名、时间、原因，不要凭感觉补双倍剂量。"],
      ["药物过敏", "过敏药物、表现、发生时间应长期记忆，复诊和急诊都要主动告知。"]
    ]
  },
  {
    id: "lifestyle",
    name: "生活方式知识库",
    icon: "salad",
    image: medicalImages.lifestyle,
    items: [
      ["糖尿病饮食记录", "记录主食量、餐后血糖、夜间低血糖线索，比只说少吃更有用。"],
      ["血压管理", "限盐、规律运动、体重管理和睡眠都影响血压控制。"],
      ["睡眠卫生", "固定作息、减少睡前屏幕、避免晚间咖啡因，持续失眠应就医评估。"],
      ["运动记录", "慢病患者记录运动类型、时长、心率和不适，复诊时可用于调整建议。"],
      ["体重管理", "关注腰围、体重趋势和饮食结构，不只看单日体重。"],
      ["戒烟", "咳嗽、慢阻肺、心血管风险人群尤其需要记录吸烟量和戒烟计划。"],
      ["饮酒", "夜间出汗、血压、尿酸、肝功能异常时要回顾饮酒情况。"],
      ["水分摄入", "发热、腹泻、血糖高时要关注脱水风险，特殊疾病需听医嘱限水。"],
      ["家庭监测", "血压计、血糖仪、体温计记录应包含时间和状态。"],
      ["陪诊沟通", "就诊前整理三件事：最担心的问题、最近变化、想让医生确认的决定。"],
      ["报告归档", "按时间保存报告，标注异常指标和医生解释，方便长期追踪。"],
      ["复诊提醒", "提前一天确认挂号、交通、空腹要求、资料和陪诊人。"]
    ]
  }
];

const layeredKnowledge = knowledgeLayers.flatMap((layer) =>
  layer.items.map(([title, content], index) => ({
    id: `${layer.id}-${index}`,
    layer: layer.id,
    category: layer.name,
    title,
    content,
    image: layer.image,
    icon: layer.icon,
    tags: [layer.name.replace("知识库", ""), title]
  }))
);

const fallbackData = {
  cases: caseLibrary,
  knowledge: layeredKnowledge,
  memories: [
    { category: "个人信息", key: "常用科室", value: "内分泌科" },
    { category: "就医偏好", key: "提醒偏好", value: "复诊前一天晚间提醒" },
    { category: "风险关注", key: "低血糖风险", value: "夜间出汗时记录当时血糖" }
  ],
  reminders: [
    { type: "复诊提醒", title: "内分泌科复诊", content: "提前准备血糖记录、检查报告、当前用药清单。", priority: "high" },
    { type: "材料准备", title: "用药清单待确认", content: "就诊前确认药名、剂量、服药时间。", priority: "medium" },
    { type: "家属同步", title: "陪诊摘要", content: "把问诊重点同步给陪诊家属。", priority: "medium" }
  ],
  records: [],
  conversations: []
};

let appData = JSON.parse(JSON.stringify(fallbackData));
let currentConversationId = null;
let isWaiting = false;
let providerState = { active_provider: "", providers: [] };
let selectedProviderId = "";
let lastTrace = { route: "", actions: [], knowledge: [], memories: [], records: [], reminders: [], safety: [], source: "", provider: "", model: "", latency: 0, firstToken: 0 };
let typingTimer = null;
let selectedKnowledgeLayer = "cases";
let activeRequestController = null;

document.addEventListener("DOMContentLoaded", async () => {
  applyTheme();
  bindEvents();
  renderSuggestions();
  renderThemeOptions();
  await loadAppData();
  await loadProviders();
  renderAll();
  openInitialView();
  refreshIcons();
});

function bindEvents() {
  $("#chatForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const text = $("#messageInput").value.trim();
    if (!text || isWaiting) return;
    $("#messageInput").value = "";
    resizeInput();
    $("#sendBtn").disabled = true;
    closeSuggestions();
    sendMessage(text);
  });

  $("#messageInput").addEventListener("input", () => {
    $("#sendBtn").disabled = !$("#messageInput").value.trim() || isWaiting;
    resizeInput();
  });
  $("#messageInput").addEventListener("focus", openSuggestions);
  $("#messageInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#chatForm").requestSubmit();
    }
    if (event.key === "Escape") {
      closeSuggestions();
      $("#themePanel")?.classList.remove("open");
    }
  });

  $("#suggestionBtn").addEventListener("click", () => {
    $("#suggestionPanel").classList.toggle("open");
    $("#messageInput").focus();
  });
  $("#stopBtn").addEventListener("click", stopStreaming);
  $("#themeToggle").addEventListener("click", () => {
    $("#themePanel").classList.toggle("open");
  });
  $("#modelPill").addEventListener("click", () => switchView("models"));
  $("#collapseBtn").addEventListener("click", () => document.body.classList.toggle("collapsed"));
  $("#newChatIconBtn").addEventListener("click", startNewChat);
  $("#brandNewChatBtn").addEventListener("click", startNewChat);
  $("#quickDemoBtn").addEventListener("click", () => switchView("demo"));
  $("#mobileMenuBtn").addEventListener("click", () => document.body.classList.toggle("mobile-menu"));

  $$(".menu-item").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  $$(".feature-card, .loop-step").forEach((card) => {
    card.addEventListener("click", () => sendMessage(card.dataset.prompt));
  });

  $("#knowledgeSearch").addEventListener("input", () => renderKnowledge($("#knowledgeSearch").value.trim()));
  $("#modelForm").addEventListener("submit", saveProviderForm);
  $("#fetchModelsBtn").addEventListener("click", fetchSelectedModels);
  $("#providerModelSelect").addEventListener("change", () => {
    $("#providerModelInput").value = $("#providerModelSelect").value;
  });

  document.addEventListener("click", (event) => {
    if (!$("#composerWrap").contains(event.target)) closeSuggestions();
    if (!$(".side-footer")?.contains(event.target)) $("#themePanel")?.classList.remove("open");
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSuggestions();
      $("#themePanel")?.classList.remove("open");
      closeDialog();
    }
  });
}

function applyTheme() {
  const requested = new URLSearchParams(window.location.search).get("theme");
  if (requested && themes.some((item) => item.id === requested)) {
    localStorage.setItem("yipeibang-theme", requested);
  }
  const saved = localStorage.getItem("yipeibang-theme");
  const theme = saved === "dark" ? "midnight" : saved || "clinical";
  document.body.dataset.theme = themes.some((item) => item.id === theme) ? theme : "clinical";
  document.body.classList.toggle("dark", document.body.dataset.theme === "midnight");
}

function setTheme(themeId) {
  const theme = themes.some((item) => item.id === themeId) ? themeId : "clinical";
  document.body.dataset.theme = theme;
  document.body.classList.toggle("dark", theme === "midnight");
  localStorage.setItem("yipeibang-theme", theme);
  renderThemeOptions();
  updateThemeLabel();
  showToast(`已切换到${themes.find((item) => item.id === theme)?.name || "新主题"}`);
}

function renderThemeOptions() {
  const box = $("#themeOptions");
  if (!box) return;
  const current = document.body.dataset.theme || "clinical";
  box.innerHTML = themes.map((theme) => `
    <button type="button" class="theme-option ${theme.id === current ? "active" : ""}" data-theme="${escapeAttr(theme.id)}">
      <span class="theme-swatches">${theme.swatches.map((color) => `<i style="background:${escapeAttr(color)}"></i>`).join("")}</span>
      <span>
        <strong>${escapeHtml(theme.name)}</strong>
        <small>${escapeHtml(theme.desc)}</small>
      </span>
    </button>
  `).join("");
  $$(".theme-option").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.theme));
  });
  updateThemeLabel();
}

function updateThemeLabel() {
  const current = themes.find((item) => item.id === (document.body.dataset.theme || "clinical")) || themes[0];
  const label = $("#themeToggle span");
  if (label) label.textContent = current.name;
}

async function loadAppData() {
  try {
    const [appResponse, casesResponse, knowledgeResponse, profileResponse, recordsResponse, remindersResponse] = await Promise.all([
      fetch("/api/app-data"),
      fetch("/api/cases"),
      fetch("/api/knowledge"),
      fetch("/api/profile"),
      fetch("/api/health-records"),
      fetch("/api/reminders")
    ]);
    if (!appResponse.ok) throw new Error("app-data failed");
    const data = await appResponse.json();
    const casesData = casesResponse.ok ? await casesResponse.json() : { cases: data.cases || [] };
    const knowledgeData = knowledgeResponse.ok ? await knowledgeResponse.json() : { knowledge: data.knowledge || [] };
    const profileData = profileResponse.ok ? await profileResponse.json() : { sections: {} };
    const recordsData = recordsResponse.ok ? await recordsResponse.json() : { records: data.records || [] };
    const remindersData = remindersResponse.ok ? await remindersResponse.json() : { reminders: data.reminders || [] };
    const memories = [
      ...(profileData.sections?.long_term_memory || []),
      ...(data.memories || [])
    ];
    appData = {
      ...fallbackData,
      ...data,
      cases: normalizeCases(casesData.cases?.length ? casesData.cases : fallbackData.cases),
      knowledge: normalizeKnowledge(knowledgeData.knowledge?.length ? knowledgeData.knowledge : layeredKnowledge),
      memories: memories.length ? normalizeMemories(memories) : fallbackData.memories,
      records: normalizeRecords(recordsData.records || data.records || []),
      reminders: normalizeReminders(remindersData.reminders?.length ? remindersData.reminders : data.reminders || []),
      conversations: data.conversations || []
    };
    if (!appData.reminders.length) appData.reminders = fallbackData.reminders;
  } catch (error) {
    console.warn("使用本地演示数据", error);
    showToast("数据接口暂不可用，已切换本地演示数据");
  }
}

async function refreshConversations() {
  try {
    const response = await fetch("/api/conversations");
    const data = await response.json();
    appData.conversations = data.conversations || [];
    renderConversations();
  } catch (error) {
    console.warn("历史对话加载失败", error);
  }
}

async function loadProviders() {
  try {
    const response = await fetch("/api/providers");
    if (!response.ok) throw new Error("providers failed");
    providerState = await response.json();
    selectedProviderId = providerState.active_provider || providerState.providers?.[0]?.id || "";
    renderProviders();
  } catch (error) {
    console.warn("模型配置加载失败", error);
    providerState = {
      active_provider: "anyrouter",
      providers: [
        { id: "anyrouter", name: "AnyRouter", base_url: "https://anyrouter.top", model: "", models: [], enabled: true, api_key_set: false, api_key_preview: "" },
        { id: "elysia", name: "Elysia", base_url: "https://elysia.h-e.top", model: "", models: [], enabled: true, api_key_set: false, api_key_preview: "" }
      ]
    };
    selectedProviderId = providerState.active_provider;
    renderProviders();
  }
}

function renderAll() {
  renderHomeStatus();
  renderConversations();
  renderProfile();
  renderCases();
  renderKnowledge();
  renderRecords();
  renderReminders();
  renderProviders();
  renderDemoRoutes();
}

function renderHomeStatus() {
  if (!$("#homeCaseCount")) return;
  $("#homeCaseCount").textContent = appData.cases?.length || 0;
  $("#homeKnowledgeCount").textContent = appData.knowledge?.length || 0;
  $("#homeRecordCount").textContent = appData.records?.length || 0;
  $("#homeReminderCount").textContent = (appData.reminders || []).filter((item) => item.status !== "done" && !item.done).length;
}

function openInitialView() {
  const view = new URLSearchParams(window.location.search).get("view");
  if (view && $(`#view-${view}`)) switchView(view);
}

function getSelectedProvider() {
  return providerState.providers.find((item) => item.id === selectedProviderId)
    || providerState.providers.find((item) => item.id === providerState.active_provider)
    || providerState.providers[0]
    || null;
}

function getActiveProvider() {
  return providerState.providers.find((item) => item.id === providerState.active_provider) || getSelectedProvider();
}

function renderProviders() {
  const providers = providerState.providers || [];
  if (!providers.length || !$("#providerList")) return;
  const active = getActiveProvider();
  if (!selectedProviderId) selectedProviderId = active?.id || providers[0].id;
  $("#providerList").innerHTML = providers.map((item) => `
    <button type="button" class="provider-card ${item.id === selectedProviderId ? "active" : ""}" data-id="${escapeAttr(item.id)}">
      <span class="provider-icon"><i data-lucide="${item.id === "custom" ? "settings-2" : "radio-tower"}"></i></span>
      <span>
        <strong>${escapeHtml(item.name || item.id)}</strong>
        <small>${item.model ? "模型已选择" : "未选择模型"}</small>
      </span>
      <em>${item.id === providerState.active_provider ? "使用中" : item.api_key_set ? item.api_key_preview : "未配置"}</em>
    </button>
  `).join("");
  $$(".provider-card").forEach((button) => {
    button.addEventListener("click", () => {
      selectedProviderId = button.dataset.id;
      renderProviders();
    });
  });
  renderProviderForm();
  updateModelPill();
  refreshIcons();
}

function renderProviderForm() {
  const provider = getSelectedProvider();
  if (!provider) return;
  $("#providerName").value = provider.name || "";
  $("#providerBaseUrl").value = provider.base_url || "";
  $("#providerApiKey").value = "";
  $("#providerApiKey").placeholder = provider.api_key_set ? `已保存 ${provider.api_key_preview}，留空沿用` : "请输入 API Key";
  const models = provider.models?.length ? provider.models : (provider.model ? [provider.model] : []);
  $("#providerModelSelect").innerHTML = models.length
    ? models.map((model, index) => `<option value="${escapeAttr(model)}" ${model === provider.model ? "selected" : ""}>模型通道 ${index + 1}</option>`).join("")
    : `<option value="">暂无模型列表</option>`;
  $("#providerModelInput").value = "";
  $("#providerModelInput").placeholder = provider.model ? "已选择模型，留空沿用" : "可手动输入模型名";
  $("#modelStatus").textContent = `${provider.name || provider.id} · ${provider.api_key_set ? "Key 已配置" : "待配置"}`;
}

function updateModelPill() {
  const active = getActiveProvider();
  $("#modelPillText").textContent = active ? (active.name || active.id) : "模型";
}

async function fetchSelectedModels() {
  const provider = getSelectedProvider();
  if (!provider) return;
  $("#modelStatus").textContent = "正在获取模型...";
  $("#fetchModelsBtn").disabled = true;
  try {
    const response = await fetch(`/api/providers/${encodeURIComponent(provider.id)}/models`);
    const data = await response.json();
    if (!response.ok || data.success === false) throw new Error(data.error || "获取失败");
    await loadProviders();
    selectedProviderId = provider.id;
    $("#modelStatus").textContent = `已获取 ${data.models.length} 个模型`;
  } catch (error) {
    $("#modelStatus").textContent = `获取失败：${error.message}`;
  } finally {
    $("#fetchModelsBtn").disabled = false;
    renderProviders();
  }
}

async function saveProviderForm(event) {
  event.preventDefault();
  const provider = getSelectedProvider();
  const model = $("#providerModelInput").value.trim() || $("#providerModelSelect").value;
  const payload = {
    id: provider?.id || "custom",
    name: $("#providerName").value.trim() || provider?.name || "自定义",
    base_url: $("#providerBaseUrl").value.trim(),
    api_key: $("#providerApiKey").value.trim(),
    model,
    enabled: true,
    set_active: true
  };
  $("#modelStatus").textContent = "正在保存...";
  try {
    const response = await fetch("/api/providers/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok || data.success === false) throw new Error(data.error || "保存失败");
    await loadProviders();
    selectedProviderId = data.active_provider;
    $("#modelStatus").textContent = "已保存并启用";
  } catch (error) {
    $("#modelStatus").textContent = `保存失败：${error.message}`;
  } finally {
    renderProviders();
  }
}

function renderSuggestions() {
  $("#suggestionList").innerHTML = quickQuestions.map((text) => `
    <div class="suggestion-item">
      <div class="suggestion-text">${escapeHtml(text)}</div>
      <div class="suggestion-actions">
        <button class="suggestion-action copy-question" type="button" title="复制" data-text="${escapeAttr(text)}"><i data-lucide="copy"></i></button>
        <button class="suggestion-action send-question" type="button" title="发送" data-text="${escapeAttr(text)}"><i data-lucide="send-horizontal"></i></button>
      </div>
    </div>
  `).join("");

  $$(".send-question").forEach((button) => {
    button.addEventListener("click", () => {
      closeSuggestions();
      sendMessage(button.dataset.text);
    });
  });
  $$(".copy-question").forEach((button) => {
    button.addEventListener("click", async () => {
      await copyText(button.dataset.text);
      button.innerHTML = '<i data-lucide="check"></i>';
      refreshIcons();
      setTimeout(() => {
        button.innerHTML = '<i data-lucide="copy"></i>';
        refreshIcons();
      }, 900);
    });
  });
}

function renderConversations() {
  const list = appData.conversations || [];
  const markup = list.length ? list.map((item) => `
    <button class="conversation-item ${item.id === currentConversationId ? "active" : ""}" data-id="${escapeAttr(item.id)}">
      <strong>${escapeHtml(item.title || "新对话")}</strong>
      <span>${Number(item.message_count || 0)} 条消息</span>
    </button>
  `).join("") : `<div class="empty-note">还没有历史对话</div>`;
  $("#conversationList").innerHTML = markup;
  $("#historyPageList").innerHTML = list.length ? list.map((item) => `
    <article class="history-row" data-id="${escapeAttr(item.id)}">
      <h3>${escapeHtml(item.title || "新对话")}</h3>
      <p>${Number(item.message_count || 0)} 条消息，点击继续。</p>
    </article>
  `).join("") : `<article class="history-row"><h3>暂无历史</h3><p>开始一次对话后会自动保存。</p></article>`;
  $("#historyCount").textContent = `${list.length} 条`;

  $$(".conversation-item, .history-row[data-id]").forEach((item) => {
    item.addEventListener("click", () => loadConversation(item.dataset.id));
  });
}

function renderProfile() {
  $("#profileGrid").innerHTML = `
    <article class="interactive-panel full-span">
      <div class="panel-title-row">
        <h3>新增长期记忆</h3>
        <button class="mini-secondary" id="clearDemoBtn" type="button"><i data-lucide="trash-2"></i><span>清空演示数据</span></button>
      </div>
      <div class="inline-form">
        <input id="memoryKeyInput" placeholder="例如：药物过敏">
        <input id="memoryValueInput" placeholder="例如：青霉素过敏">
        <button class="mini-primary" id="addMemoryBtn" type="button"><i data-lucide="plus"></i><span>加入档案</span></button>
      </div>
    </article>
    ${appData.memories.slice(0, 18).map((item, index) => `
      <article class="content-card memory-card" data-index="${index}">
        <div class="card-topline">
          <span class="provider-icon"><i data-lucide="user-round-check"></i></span>
          <span>
            <button class="icon-mini edit-memory" type="button" title="编辑" data-index="${index}"><i data-lucide="pencil"></i></button>
            <button class="icon-mini delete-memory" type="button" title="删除" data-index="${index}" data-id="${escapeAttr(item.id || "")}"><i data-lucide="trash-2"></i></button>
          </span>
        </div>
        <h3>${escapeHtml(item.key)}</h3>
        <p>${escapeHtml(item.value)}</p>
        <div class="meta-row"><span class="tag">${escapeHtml(item.category)}</span></div>
      </article>
    `).join("")}
  `;
  $("#addMemoryBtn").addEventListener("click", async () => {
    const key = $("#memoryKeyInput").value.trim();
    const value = $("#memoryValueInput").value.trim();
    if (!key || !value) return;
    const saved = await createMemory({ category: "用户档案", key, value, source: "用户手动维护" });
    appData.memories = mergeMemories([{ id: saved?.id, category: "用户档案", key, value }], appData.memories);
    showToast("已加入长期档案");
    renderProfile();
    renderRecords();
  });
  $("#clearDemoBtn").addEventListener("click", async () => {
    if (!confirm("确认清空健康记录、提醒和动作日志？长期档案会保留，便于继续演示。")) return;
    await resetDemoData();
    await refreshRuntimeData();
    showToast("演示数据已清空");
  });
  $$(".edit-memory").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.index);
      const item = appData.memories[index];
      const next = prompt("修改记忆内容", item.value);
      if (next === null) return;
      appData.memories[index] = { ...item, value: next.trim() || item.value };
      if (item.id) updateMemoryValue(item.id, appData.memories[index].value);
      showToast("已更新页面档案");
      renderProfile();
      renderRecords();
    });
  });
  $$(".delete-memory").forEach((button) => {
    button.addEventListener("click", async () => {
      const index = Number(button.dataset.index);
      if (button.dataset.id) await deleteMemory(button.dataset.id);
      appData.memories.splice(index, 1);
      showToast("记忆已删除");
      renderProfile();
      renderRecords();
    });
  });
  refreshIcons();
}

function renderCases() {
  $("#topRight").textContent = "";
  const grid = $("#view-cases #caseGrid");
  if (!grid) return;
  grid.innerHTML = appData.cases.map((item) => `
    <article class="content-card clickable case-card" data-prompt="${escapeAttr(item.prompt)}">
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.patient || "")}</p>
      <p>${escapeHtml(item.scenario || "")}</p>
      <div class="meta-row">${(item.tags || []).slice(0, 4).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
    </article>
  `).join("");
  $$(".case-card").forEach((card) => card.addEventListener("click", () => sendMessage(card.dataset.prompt)));
}

function renderKnowledge(query = "") {
  renderKnowledgeTabs();
  const normalizedQuery = query.trim();
  if (selectedKnowledgeLayer === "cases") {
    const cases = appData.cases.filter((item) => {
      if (!normalizedQuery) return true;
      return `${item.title} ${item.patient} ${item.scenario} ${(item.tags || []).join(" ")}`.includes(normalizedQuery);
    });
    $("#knowledgeCount").textContent = `${cases.length} 个病例`;
    $("#knowledgeGrid").innerHTML = cases.map((item) => `
      <article class="case-library-card">
        <img src="${escapeAttr(item.image)}" alt="${escapeAttr(item.title)}">
        <div>
          <div class="meta-row">${(item.tags || []).slice(0, 3).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.patient)}</p>
          <p>${escapeHtml(item.scenario)}</p>
          <div class="card-actions">
            <button class="mini-primary ask-case" type="button" data-prompt="${escapeAttr(item.prompt)}"><i data-lucide="send-horizontal"></i><span>按此病例提问</span></button>
            <button class="mini-secondary copy-case" type="button" data-prompt="${escapeAttr(item.prompt)}"><i data-lucide="copy"></i><span>复制问题</span></button>
            <button class="mini-secondary case-detail" type="button" data-id="${escapeAttr(item.id)}"><i data-lucide="file-search"></i><span>看详情</span></button>
          </div>
        </div>
      </article>
    `).join("") || emptyPanel("没有找到病例", "换个症状、疾病或指标关键词试试。");
    bindCaseButtons();
    refreshIcons();
    return;
  }

  const items = appData.knowledge.filter((item) => {
    if (selectedKnowledgeLayer !== "all" && item.layer !== selectedKnowledgeLayer) return false;
    if (!normalizedQuery) return true;
    return `${item.category} ${item.title || ""} ${item.content} ${(item.tags || []).join(" ")}`.includes(normalizedQuery);
  });
  $("#knowledgeCount").textContent = `${items.length} 条`;
  $("#knowledgeGrid").innerHTML = items.map((item) => `
    <article class="knowledge-card">
      <img src="${escapeAttr(item.image || medicalImages.report)}" alt="${escapeAttr(item.title || item.category)}">
      <div>
        <div class="knowledge-title">
          <span class="provider-icon"><i data-lucide="${escapeAttr(item.icon || "book-open")}"></i></span>
          <h3>${escapeHtml(item.title || item.category || "知识")}</h3>
        </div>
        <p>${escapeHtml(item.content)}</p>
        ${item.red_flags?.length ? `<div class="risk-inline"><strong>红旗</strong>${item.red_flags.slice(0, 4).map((flag) => `<span>${escapeHtml(flag)}</span>`).join("")}</div>` : ""}
        ${item.record_fields?.length ? `<div class="field-inline"><strong>记录字段</strong>${item.record_fields.slice(0, 5).map((field) => `<span>${escapeHtml(field)}</span>`).join("")}</div>` : ""}
        ${item.when_to_seek_care ? `<p class="care-line"><strong>何时就医：</strong>${escapeHtml(item.when_to_seek_care)}</p>` : ""}
        ${item.source ? `<p class="source-line">来源：${escapeHtml(item.source)}</p>` : ""}
        <div class="meta-row">${(item.tags || []).slice(0, 4).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
        <div class="card-actions">
          <button class="mini-primary ask-knowledge" type="button" data-question="${escapeAttr(item.title || item.category)}"><i data-lucide="message-circle"></i><span>追问</span></button>
          <button class="mini-secondary remember-knowledge" type="button" data-title="${escapeAttr(item.title || item.category)}" data-content="${escapeAttr(item.content)}"><i data-lucide="bookmark-plus"></i><span>加入档案</span></button>
          <button class="mini-secondary knowledge-detail" type="button" data-id="${escapeAttr(item.id)}"><i data-lucide="panel-right-open"></i><span>详情</span></button>
        </div>
      </div>
    </article>
  `).join("") || emptyPanel("没有找到知识", "换个关键词试试。");
  bindKnowledgeButtons();
  refreshIcons();
}

function renderKnowledgeTabs() {
  const tabs = [
    { id: "cases", name: "病例库", icon: "folder-heart" },
    ...knowledgeLayers.map((layer) => ({ id: layer.id, name: layer.name.replace("知识库", ""), icon: layer.icon })),
    { id: "all", name: "全部", icon: "layout-grid" }
  ];
  $("#knowledgeTabs").innerHTML = tabs.map((tab) => `
    <button type="button" class="knowledge-tab ${tab.id === selectedKnowledgeLayer ? "active" : ""}" data-layer="${escapeAttr(tab.id)}">
      <i data-lucide="${escapeAttr(tab.icon)}"></i><span>${escapeHtml(tab.name)}</span>
    </button>
  `).join("");
  $$(".knowledge-tab").forEach((button) => {
    button.addEventListener("click", () => {
      selectedKnowledgeLayer = button.dataset.layer;
      renderKnowledge($("#knowledgeSearch").value.trim());
    });
  });
}

function bindCaseButtons() {
  $$(".ask-case").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));
  $$(".copy-case").forEach((button) => button.addEventListener("click", async () => {
    await copyText(button.dataset.prompt);
    showToast("病例问题已复制");
  }));
  $$(".case-detail").forEach((button) => button.addEventListener("click", () => showCaseDetail(button.dataset.id)));
}

function bindKnowledgeButtons() {
  $$(".ask-knowledge").forEach((button) => {
    button.addEventListener("click", () => {
      switchView("chat");
      $("#messageInput").value = `${button.dataset.question} 是什么意思？需要注意什么？`;
      $("#sendBtn").disabled = false;
      $("#messageInput").focus();
    });
  });
  $$(".remember-knowledge").forEach((button) => {
    button.addEventListener("click", async () => {
      const saved = await createMemory({ category: "知识收藏", key: button.dataset.title, value: button.dataset.content, source: "知识库收藏" });
      appData.memories = mergeMemories([{ id: saved?.id, category: "知识收藏", key: button.dataset.title, value: button.dataset.content }], appData.memories);
      renderProfile();
      renderRecords();
      button.querySelector("span").textContent = "已加入";
      showToast("已加入我的档案");
    });
  });
  $$(".knowledge-detail").forEach((button) => button.addEventListener("click", () => showKnowledgeDetail(button.dataset.id)));
}

function renderRecords() {
  const memoryRecords = appData.memories
    .filter((item) => /指标|风险|健康|用药|科室|任务/.test(item.category + item.key + item.value))
    .map((item) => ({ type: item.category, value: `${item.key}：${item.value}`, note: "来自长期记忆", risk_level: /风险|异常|偏高|胸/.test(item.value) ? "warning" : "normal" }));
  const list = [...(appData.records || []), ...memoryRecords].slice(0, 12);
  $("#recordGrid").innerHTML = `
    <article class="interactive-panel full-span">
      <div class="panel-title-row">
        <h3>指标趋势</h3>
        <span class="tag">${list.length} 条记录</span>
      </div>
      <div class="trend-strip">
        ${list.slice(0, 8).map((item) => `<span class="${item.risk_level === "warning" ? "warn" : ""}" style="height:${trendHeight(item)}%"></span>`).join("") || "<em>暂无趋势数据</em>"}
      </div>
    </article>
    <article class="interactive-panel full-span">
      <h3>记录新的健康信息</h3>
      <div class="inline-form">
        <input id="recordNameInput" placeholder="例如：血压 / 血糖 / 症状">
        <input id="recordValueInput" placeholder="例如：138/86，轻微头胀">
        <button class="mini-primary" id="addRecordBtn" type="button"><i data-lucide="activity"></i><span>保存记录</span></button>
      </div>
    </article>
    ${list.map((item) => `
      <article class="record-card record-rich">
        <img src="${escapeAttr(recordImage(item))}" alt="${escapeAttr(recordTitle(item))}">
        <h3>${escapeHtml(recordTitle(item))}</h3>
        <p>${escapeHtml(recordValue(item))}</p>
        <div class="meta-row"><span class="tag">${escapeHtml(recordTypeLabel(item.type))}</span><span class="tag">${escapeHtml(item.risk_level === "warning" ? "需关注" : "正常记录")}</span></div>
        <button class="mini-secondary ask-record" type="button" data-question="${escapeAttr(recordTitle(item) + ' ' + recordValue(item))}"><i data-lucide="message-circle"></i><span>让医陪帮分析</span></button>
      </article>
    `).join("") || emptyPanel("还没有健康记录", "你可以手动记录，也可以在对话中说“血压150/96”让系统自动沉淀。")}
  `;
  $("#addRecordBtn").addEventListener("click", async () => {
    const key = $("#recordNameInput").value.trim();
    const value = $("#recordValueInput").value.trim();
    if (!key || !value) return;
    const payload = {
      type: inferRecordType(key + value),
      value,
      unit: inferRecordUnit(key + value),
      note: key,
      risk_level: /偏高|胸痛|呼吸困难|头晕|150|8\./.test(value) ? "warning" : "normal"
    };
    const saved = await createHealthRecord(payload);
    appData.records = [{ ...payload, id: saved?.id, measured_at: new Date().toLocaleString("zh-CN", { hour12: false }) }, ...(appData.records || [])];
    showToast("健康记录已保存");
    renderRecords();
  });
  $$(".ask-record").forEach((button) => button.addEventListener("click", () => sendMessage(`${button.dataset.question}，帮我分析需要注意什么`)));
  refreshIcons();
}

function renderReminders(extraActions = []) {
  const generated = extraActions
    .filter((item) => /提醒|同步|摘要|清单|提纲/.test(item))
    .map((item) => ({ type: "对话触发", title: item, content: "已根据对话自动生成。", priority: "high" }));
  const reminders = [...generated, ...appData.reminders].slice(0, 12);
  $("#reminderGrid").innerHTML = `
    <article class="interactive-panel">
      <h3>创建主动提醒</h3>
      <div class="inline-form stacked">
        <input id="reminderTitleInput" placeholder="例如：明晚8点准备复诊材料">
        <button class="mini-primary" id="addReminderBtn" type="button"><i data-lucide="bell-plus"></i><span>创建提醒</span></button>
      </div>
    </article>
    ${reminders.map((item, index) => `
      <article class="reminder-row reminder-rich ${item.done || item.status === "done" ? "done" : ""}">
        <img src="${escapeAttr(reminderImage(item))}" alt="${escapeAttr(item.title)}">
        <div>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.content || item.source_reason || (item.checklist || []).join("；") || "主动服务提醒")}</p>
          <div class="meta-row"><span class="tag">${escapeHtml(item.type || "提醒")}</span><span class="tag">${escapeHtml(priorityLabel(item.priority))}</span><span class="tag">${escapeHtml(item.due_time || item.triggerTime || "待定")}</span></div>
          ${(item.checklist || []).length ? `<ul class="mini-checklist">${item.checklist.slice(0, 4).map((todo) => `<li>${escapeHtml(todo)}</li>`).join("")}</ul>` : ""}
          <div class="card-actions">
            <button class="mini-secondary done-reminder" type="button" data-index="${index}" data-id="${escapeAttr(item.id || "")}"><i data-lucide="check"></i><span>${item.done || item.status === "done" ? "已完成" : "标记完成"}</span></button>
            <button class="mini-secondary snooze-reminder" type="button" data-index="${index}" data-id="${escapeAttr(item.id || "")}"><i data-lucide="clock-3"></i><span>延期</span></button>
            <button class="mini-secondary delete-reminder" type="button" data-index="${index}" data-id="${escapeAttr(item.id || "")}"><i data-lucide="trash-2"></i><span>删除</span></button>
            <button class="mini-primary ask-reminder" type="button" data-title="${escapeAttr(item.title)}"><i data-lucide="send-horizontal"></i><span>生成执行清单</span></button>
          </div>
        </div>
      </article>
    `).join("")}
  `;
  $("#addReminderBtn").addEventListener("click", async () => {
    const title = $("#reminderTitleInput").value.trim();
    if (!title) return;
    const payload = {
      title,
      due_time: title.includes("8点") ? "20:00" : new Date().toLocaleString("zh-CN", { hour12: false }),
      priority: /复诊|急|明天/.test(title) ? "high" : "medium",
      checklist: ["确认就医资料", "提前检查交通和挂号", "完成后更新健康记录"],
      source_reason: "用户手动创建"
    };
    const saved = await createReminder(payload);
    appData.reminders = [{ ...payload, id: saved?.id, type: "主动提醒", content: "用户手动创建，已保存到提醒中心。" }, ...appData.reminders];
    showToast("提醒已创建");
    renderReminders(extraActions);
  });
  $$(".done-reminder").forEach((button) => button.addEventListener("click", async () => {
    const index = Number(button.dataset.index);
    const target = reminders[index];
    const done = !(target.done || target.status === "done");
    if (button.dataset.id) await updateReminder(button.dataset.id, { status: done ? "done" : "pending" });
    if (appData.reminders[index]) appData.reminders[index] = { ...appData.reminders[index], done, status: done ? "done" : "pending" };
    showToast(done ? "已标记完成" : "已恢复待办");
    renderReminders(extraActions);
  }));
  $$(".snooze-reminder").forEach((button) => button.addEventListener("click", async () => {
    const next = prompt("延期到什么时候？", "明天 20:00");
    if (!next) return;
    const index = Number(button.dataset.index);
    if (button.dataset.id) await updateReminder(button.dataset.id, { due_time: next });
    if (appData.reminders[index]) appData.reminders[index] = { ...appData.reminders[index], due_time: next };
    showToast("提醒已延期");
    renderReminders(extraActions);
  }));
  $$(".delete-reminder").forEach((button) => button.addEventListener("click", async () => {
    const index = Number(button.dataset.index);
    if (button.dataset.id) await deleteReminder(button.dataset.id);
    appData.reminders.splice(index, 1);
    showToast("提醒已删除");
    renderReminders(extraActions);
  }));
  $$(".ask-reminder").forEach((button) => button.addEventListener("click", () => sendMessage(`${button.dataset.title}，帮我生成详细执行清单`)));
  refreshIcons();
}

function recordImage(item) {
  const text = `${item.category || ""} ${item.key || ""} ${item.type || ""} ${item.note || ""} ${item.value || ""}`;
  if (/血压/.test(text)) return medicalImages.pressure;
  if (/血糖|糖尿病|低血糖/.test(text)) return medicalImages.diabetes;
  if (/用药|药/.test(text)) return medicalImages.medicine;
  if (/报告|指标|体检/.test(text)) return medicalImages.report;
  return medicalImages.doctor;
}

function reminderImage(item) {
  const text = `${item.type || ""} ${item.title || ""} ${item.content || ""} ${item.source_reason || ""}`;
  if (/家属|同步|陪诊/.test(text)) return medicalImages.family;
  if (/材料|清单|报告/.test(text)) return medicalImages.report;
  if (/复诊|医院/.test(text)) return medicalImages.hospital;
  return medicalImages.elder;
}

function emptyPanel(title, text) {
  return `<article class="interactive-panel full-span"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(text)}</p></article>`;
}

function switchView(viewName) {
  const titles = {
    chat: "医陪帮",
    history: "历史对话",
    profile: "我的档案",
    knowledge: "知识库浏览",
    records: "健康记录",
    reminders: "提醒中心",
    models: "模型设置",
    demo: "演示路线"
  };
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${viewName}`));
  $$(".menu-item").forEach((button) => button.classList.toggle("active", button.dataset.view === viewName));
  $("#topTitle").textContent = titles[viewName] || "医陪帮";
  document.body.classList.remove("mobile-menu");
  closeSuggestions();
  refreshIcons();
}

function startNewChat() {
  currentConversationId = null;
  $("#messagesContainer").innerHTML = "";
  $("#homePanel").style.display = "grid";
  switchView("chat");
  renderConversations();
}

async function loadConversation(id) {
  if (!id) return;
  try {
    const response = await fetch(`/api/conversations/${encodeURIComponent(id)}`);
    const data = await response.json();
    currentConversationId = id;
    $("#homePanel").style.display = "none";
    $("#messagesContainer").innerHTML = "";
    (data.messages || []).forEach((msg) => addMessage(msg.role === "assistant" ? "assistant" : "user", msg.content, false));
    switchView("chat");
    renderConversations();
  } catch (error) {
    console.warn("对话加载失败", error);
  }
}

async function sendMessage(text) {
  if (!text || isWaiting) return;
  switchView("chat");
  $("#homePanel").style.display = "none";
  isWaiting = true;
  activeRequestController = new AbortController();
  $("#sendBtn").disabled = true;
  $("#stopBtn").classList.add("visible");
  const activeProvider = getActiveProvider();
  const requestModel = activeProvider?.model || "";
  lastTrace = { route: "", actions: [], knowledge: [], memories: [], records: [], reminders: [], safety: [], source: "", provider: activeProvider?.name || activeProvider?.id || "", model: requestModel, latency: 0, firstToken: 0 };
  addMessage("user", text, false);
  const assistantMessage = addMessage("assistant", "", true);
  let fullText = "";
  let displayedText = "";
  let pendingText = "";
  let responseStarted = false;
  let responseDone = false;

  const flushTyping = () => {
    if (typingTimer) return;
    typingTimer = setInterval(() => {
      if (!pendingText) {
        clearInterval(typingTimer);
        typingTimer = null;
        if (responseDone) {
          updateMessage(assistantMessage, displayedText, false);
          renderTrace(assistantMessage);
          renderReminders(lastTrace.actions);
        }
        return;
      }
      displayedText += pendingText.slice(0, 1);
      pendingText = pendingText.slice(1);
      updateMessage(assistantMessage, displayedText, true);
    }, 13);
  };

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: activeRequestController.signal,
      body: JSON.stringify({
        text,
        conversation_id: currentConversationId,
        provider_id: activeProvider?.id,
        model: requestModel
      })
    });
    if (!response.ok || !response.body) throw new Error("stream failed");
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";
      for (const chunk of chunks) {
        const event = parseSse(chunk);
        if (!event) continue;
        if (event.event === "intent") {
          lastTrace.route = event.data.route || "";
          updateThinking(assistantMessage, "正在判断问题类型", routeLabel(lastTrace.route));
        }
        if (event.event === "thinking") updateThinking(assistantMessage, "正在组织回答", event.data.step || "处理中");
        if (event.event === "knowledge") lastTrace.knowledge = event.data.results || [];
        if (event.event === "memory") {
          lastTrace.memories = normalizeMemories(event.data.memories || []);
          if (lastTrace.memories.length) {
            appData.memories = mergeMemories(lastTrace.memories, appData.memories);
            renderProfile();
            renderRecords();
          }
          updateThinking(assistantMessage, "正在更新记忆", `${lastTrace.memories.length} 条`);
        }
        if (event.event === "knowledge") updateThinking(assistantMessage, "正在检索知识库", `${lastTrace.knowledge.length} 条`);
        if (event.event === "action") {
          lastTrace.actions = event.data.actions || [];
          lastTrace.records = event.data.records_preview || [];
          updateThinking(assistantMessage, "正在调用模型", activeProvider?.name || "API");
        }
        if (event.event === "token") {
          fullText += event.data.content || "";
          pendingText += event.data.content || "";
          if (!responseStarted) {
            responseStarted = true;
            assistantMessage.classList.remove("thinking");
          }
          flushTyping();
        }
        if (event.event === "done") {
          currentConversationId = event.data.conversation_id || currentConversationId;
          lastTrace.source = event.data.source || "";
          lastTrace.provider = event.data.provider || lastTrace.provider;
          lastTrace.model = event.data.model || lastTrace.model;
          if (event.data.action_trace) {
            const trace = event.data.action_trace;
            lastTrace.route = trace.route || lastTrace.route;
            lastTrace.actions = trace.actions || lastTrace.actions;
            lastTrace.knowledge = trace.knowledge_used || lastTrace.knowledge;
            lastTrace.memories = normalizeMemories(trace.memories_written || []);
            lastTrace.records = trace.records_written || lastTrace.records;
            lastTrace.reminders = trace.reminders_written || [];
            lastTrace.safety = trace.safety_flags || [];
            lastTrace.provider = trace.provider || lastTrace.provider;
            lastTrace.latency = trace.latency_ms || 0;
            lastTrace.firstToken = trace.first_token_ms || 0;
            await refreshRuntimeData();
          }
          responseDone = true;
          if (!pendingText) {
            displayedText = fullText;
            updateMessage(assistantMessage, displayedText, false);
            renderTrace(assistantMessage);
            renderReminders(lastTrace.actions);
          }
        }
      }
    }
  } catch (error) {
    console.warn("对话失败", error);
    if (error.name === "AbortError") {
      updateMessage(assistantMessage, `${displayedText || fullText || "已停止生成。"}`, false);
      showToast("已停止生成");
    } else {
      updateMessage(assistantMessage, "抱歉，刚才连接模型失败。请稍后重试，或检查 API 配置。", false);
    }
  } finally {
    isWaiting = false;
    activeRequestController = null;
    $("#stopBtn").classList.remove("visible");
    $("#sendBtn").disabled = !$("#messageInput").value.trim();
    await refreshConversations();
    refreshIcons();
  }
}

function stopStreaming() {
  if (activeRequestController) {
    activeRequestController.abort();
  }
}

function addMessage(role, text, streaming) {
  const item = document.createElement("article");
  item.className = `message ${role}${streaming && role === "assistant" ? " thinking" : ""}`;
  item.innerHTML = `
    <div class="message-bubble">
      <div class="message-role">${role === "user" ? "你" : "医陪帮"}</div>
      <div class="message-content">${text ? formatMessage(text) : renderThinkingMarkup("正在理解你的问题", "马上开始回答")}${streaming ? '<span class="streaming-cursor"></span>' : ""}</div>
      <div class="message-tools"></div>
      <div class="message-actions">
        <button class="icon-mini copy-message" type="button" title="复制回答"><i data-lucide="copy"></i></button>
        ${role === "assistant" ? '<button class="icon-mini retry-message" type="button" title="重试"><i data-lucide="rotate-cw"></i></button>' : ""}
      </div>
    </div>
  `;
  $("#messagesContainer").appendChild(item);
  const copyButton = item.querySelector(".copy-message");
  if (copyButton) copyButton.addEventListener("click", async () => {
    await copyText(item.querySelector(".message-content")?.innerText || text || "");
    showToast("内容已复制");
  });
  const retryButton = item.querySelector(".retry-message");
  if (retryButton) retryButton.addEventListener("click", () => {
    const lastUser = [...$$(".message.user .message-content")].pop()?.innerText;
    if (lastUser) sendMessage(lastUser);
  });
  item.scrollIntoView({ block: "end", behavior: "smooth" });
  return item;
}

function updateMessage(item, text, streaming) {
  item.querySelector(".message-content").innerHTML = formatMessage(text || "正在整理...") + (streaming ? '<span class="streaming-cursor"></span>' : "");
  item.scrollIntoView({ block: "end", behavior: "smooth" });
}

function updateThinking(item, title, detail) {
  if (!item.classList.contains("thinking")) return;
  item.querySelector(".message-content").innerHTML = renderThinkingMarkup(title, detail) + '<span class="streaming-cursor"></span>';
  item.scrollIntoView({ block: "end", behavior: "smooth" });
}

function renderThinkingMarkup(title, detail) {
  return `
    <div class="thinking-card">
      <span class="thinking-loader"><i></i><i></i><i></i></span>
      <span>
        <strong>${escapeHtml(title)}</strong>
        <em>${escapeHtml(detail || "")}</em>
      </span>
    </div>
  `;
}

function renderTrace(item) {
  const tools = item.querySelector(".message-tools");
  const chips = [];
  if (lastTrace.source === "api") chips.push("API回答");
  const provider = providerState.providers.find((item) => item.id === lastTrace.provider || item.name === lastTrace.provider);
  if (lastTrace.source === "api" && (provider || lastTrace.provider)) chips.push(provider?.name || lastTrace.provider);
  if (lastTrace.route) chips.push(routeLabel(lastTrace.route));
  if (lastTrace.knowledge.length) chips.push(`知识 ${lastTrace.knowledge.length}`);
  if (lastTrace.memories.length) chips.push(`记忆 ${lastTrace.memories.length}`);
  if (lastTrace.records.length) chips.push(`记录 ${lastTrace.records.length}`);
  if (lastTrace.reminders.length) chips.push(`提醒 ${lastTrace.reminders.length}`);
  if (lastTrace.firstToken) chips.push(`首字 ${lastTrace.firstToken}ms`);
  if (lastTrace.actions.length) chips.push(`动作 ${lastTrace.actions.length}`);
  const sourcePanel = `
    <div class="trace-panel">
      <div class="trace-head"><i data-lucide="workflow"></i><strong>本轮动作</strong></div>
      <div class="trace-grid">
        <span>路由：${escapeHtml(routeLabel(lastTrace.route))}</span>
        <span>知识：${lastTrace.knowledge.length} 条</span>
        <span>记忆：${lastTrace.memories.length} 条</span>
        <span>记录：${lastTrace.records.length} 条</span>
        <span>提醒：${lastTrace.reminders.length} 条</span>
        <span>耗时：${lastTrace.latency || 0}ms</span>
      </div>
      ${lastTrace.knowledge.length ? `<div class="source-list">${lastTrace.knowledge.slice(0, 3).map((entry) => `<button type="button" class="source-chip" data-q="${escapeAttr(entry.title || entry.category || "知识")}">${escapeHtml(entry.title || entry.category || "知识")}</button>`).join("")}</div>` : ""}
      ${lastTrace.safety.length ? `<div class="risk-alert">识别到高风险表达：${lastTrace.safety.map((flag) => escapeHtml(flag.label)).join("、")}</div>` : ""}
    </div>
  `;
  tools.innerHTML = chips.map((chip) => `<span class="tool-chip">${escapeHtml(chip)}</span>`).join("") + sourcePanel;
  $$(".source-chip").forEach((button) => button.addEventListener("click", () => {
    selectedKnowledgeLayer = "all";
    switchView("knowledge");
    $("#knowledgeSearch").value = button.dataset.q;
    renderKnowledge(button.dataset.q);
  }));
  refreshIcons();
}

function parseSse(raw) {
  const lines = raw.split("\n").filter(Boolean);
  const eventLine = lines.find((line) => line.startsWith("event: "));
  const dataLine = lines.find((line) => line.startsWith("data: "));
  if (!dataLine) return null;
  try {
    return {
      event: eventLine ? eventLine.slice(7) : "message",
      data: JSON.parse(dataLine.slice(6))
    };
  } catch {
    return null;
  }
}

async function postJson(url, payload, method = "POST") {
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.success === false) throw new Error(data.error || "请求失败");
  return data;
}

async function createMemory(payload) {
  try {
    return await postJson("/api/profile/memory", payload);
  } catch (error) {
    showToast(`档案保存失败：${error.message}`);
    return null;
  }
}

async function createHealthRecord(payload) {
  try {
    return await postJson("/api/health-records", payload);
  } catch (error) {
    showToast(`健康记录保存失败：${error.message}`);
    return null;
  }
}

async function createReminder(payload) {
  try {
    return await postJson("/api/reminders", payload);
  } catch (error) {
    showToast(`提醒创建失败：${error.message}`);
    return null;
  }
}

async function deleteReminder(id) {
  try {
    const response = await fetch(`/api/reminders/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) throw new Error(data.error || "删除失败");
    return data;
  } catch (error) {
    showToast(`提醒删除失败：${error.message}`);
    return null;
  }
}

async function updateReminder(id, payload) {
  try {
    return await postJson(`/api/reminders/${encodeURIComponent(id)}`, payload, "PATCH");
  } catch (error) {
    showToast(`提醒更新失败：${error.message}`);
    return null;
  }
}

async function updateMemoryValue(id, value) {
  try {
    return await postJson(`/api/memories/${encodeURIComponent(id)}`, { value }, "PUT");
  } catch (error) {
    showToast(`记忆更新失败：${error.message}`);
    return null;
  }
}

async function deleteMemory(id) {
  try {
    const response = await fetch(`/api/memories/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (!response.ok) throw new Error("删除失败");
    return await response.json().catch(() => ({}));
  } catch (error) {
    showToast(`记忆删除失败：${error.message}`);
    return null;
  }
}

async function resetDemoData() {
  try {
    return await postJson("/api/demo/reset", {});
  } catch (error) {
    showToast(`清空失败：${error.message}`);
    return null;
  }
}

async function refreshRuntimeData() {
  try {
    const [profileResponse, recordsResponse, remindersResponse] = await Promise.all([
      fetch("/api/profile"),
      fetch("/api/health-records"),
      fetch("/api/reminders")
    ]);
    if (profileResponse.ok) {
      const data = await profileResponse.json();
      appData.memories = normalizeMemories(data.sections?.long_term_memory || appData.memories);
      renderProfile();
    }
    if (recordsResponse.ok) {
      const data = await recordsResponse.json();
      appData.records = normalizeRecords(data.records || []);
      renderRecords();
    }
    if (remindersResponse.ok) {
      const data = await remindersResponse.json();
      appData.reminders = normalizeReminders(data.reminders || []);
      renderReminders(lastTrace.actions);
    }
    renderHomeStatus();
  } catch (error) {
    console.warn("运行时数据刷新失败", error);
  }
}

function normalizeCases(cases) {
  return (cases || []).map((item, index) => ({
    ...item,
    id: item.id || `case-${index}`,
    patient: item.patient || item.patient_profile || item.chief_complaint || "真实病例样例",
    scenario: item.scenario || item.history || item.expected_actions?.join("、") || "就医陪诊闭环演示",
    image: normalizeImagePath(item.image || medicalImages.consult),
    prompt: item.prompt || item.qa_prompt || quickQuestions[index % quickQuestions.length],
    tags: item.tags || item.expected_intent || ["病例"]
  }));
}

function normalizeKnowledge(items) {
  const layerMap = { symptom: "symptoms", disease: "diseases", indicator: "indicators", medication: "medication", lifestyle: "lifestyle" };
  return (items || []).map((item, index) => ({
    ...item,
    id: item.id || `knowledge-${index}`,
    layer: item.layer || layerMap[item.category] || item.category || "all",
    category: knowledgeCategoryLabel(item.category || item.layer),
    title: item.title || item.category || "知识",
    content: item.content || item.summary || item.when_to_seek_care || "",
    image: normalizeImagePath(item.image || medicalImages.report),
    icon: knowledgeIcon(item.category || item.layer),
    tags: item.tags || [knowledgeCategoryLabel(item.category || item.layer), item.title || "知识"]
  })).filter((item) => item.content || item.title);
}

function normalizeRecords(records) {
  return (records || []).map((item) => ({
    ...item,
    value: item.value || item.content || "",
    note: item.note || item.type || "",
    risk_level: item.risk_level || "normal"
  }));
}

function normalizeReminders(reminders) {
  return (reminders || []).map((item) => ({
    ...item,
    type: item.type || "主动提醒",
    content: item.content || item.source_reason || "",
    priority: item.priority || "medium",
    checklist: Array.isArray(item.checklist) ? item.checklist : []
  }));
}

function normalizeMemories(memories) {
  return memories.map((item) => {
    const rawValue = item.content || item.value || "";
    const splitIndex = rawValue.indexOf("：");
    const cleanKey = item.key && item.key !== "default_user" ? item.key : "";
    return {
      id: item.id,
      category: item.category || "记忆",
      key: cleanKey || (splitIndex > 0 ? rawValue.slice(0, splitIndex) : item.source && item.source !== "default_user" ? item.source : "信息"),
      value: item.value || (splitIndex > 0 ? rawValue.slice(splitIndex + 1) : rawValue)
    };
  }).filter((item) => item.value);
}

function mergeMemories(newItems, oldItems) {
  const map = new Map();
  [...newItems, ...oldItems].forEach((item) => {
    map.set(`${item.category}-${item.key}`, item);
  });
  return Array.from(map.values());
}

function normalizeImagePath(path) {
  if (!path) return medicalImages.consult;
  if (/^https?:\/\//.test(path) || path.startsWith("./")) return path;
  return `./${path.replace(/^\/+/, "")}`;
}

function knowledgeCategoryLabel(category) {
  return {
    symptom: "症状知识库",
    symptoms: "症状知识库",
    disease: "疾病知识库",
    diseases: "疾病知识库",
    indicator: "体检指标知识库",
    indicators: "体检指标知识库",
    medication: "用药提醒知识库",
    lifestyle: "生活方式知识库"
  }[category] || category || "知识库";
}

function knowledgeIcon(category) {
  return {
    symptom: "stethoscope",
    symptoms: "stethoscope",
    disease: "heart-pulse",
    diseases: "heart-pulse",
    indicator: "file-heart",
    indicators: "file-heart",
    medication: "pill",
    lifestyle: "salad"
  }[category] || "book-open";
}

function recordTitle(item) {
  return item.note || recordTypeLabel(item.type) || item.key || "健康记录";
}

function recordValue(item) {
  const unit = item.unit ? ` ${item.unit}` : "";
  return `${item.value || ""}${unit}${item.measured_at ? ` · ${item.measured_at}` : ""}`;
}

function recordTypeLabel(type) {
  return {
    blood_pressure: "血压",
    blood_glucose: "血糖",
    temperature: "体温",
    symptom: "症状",
    sleep: "睡眠",
    medication: "用药"
  }[type] || type || "记录";
}

function inferRecordType(text) {
  if (/血压/.test(text) || /\d{2,3}\s*\/\s*\d{2,3}/.test(text)) return "blood_pressure";
  if (/血糖|糖化|低血糖/.test(text)) return "blood_glucose";
  if (/体温|发热|\d{2}(\.\d)?度/.test(text)) return "temperature";
  if (/睡眠|失眠/.test(text)) return "sleep";
  if (/药|二甲双胍|他汀|漏服/.test(text)) return "medication";
  return "symptom";
}

function inferRecordUnit(text) {
  if (/血压/.test(text) || /\d{2,3}\s*\/\s*\d{2,3}/.test(text)) return "mmHg";
  if (/血糖|糖化/.test(text)) return "mmol/L";
  if (/体温|发热|度/.test(text)) return "°C";
  return "";
}

function trendHeight(item) {
  const raw = Number(String(item.value || "").match(/[0-9]+(?:\.[0-9]+)?/)?.[0] || 0);
  if (!raw) return 28;
  if (item.type === "blood_pressure") return Math.max(24, Math.min(96, raw / 2));
  if (item.type === "blood_glucose") return Math.max(24, Math.min(96, raw * 10));
  if (item.type === "temperature") return Math.max(24, Math.min(96, (raw - 35) * 24));
  return item.risk_level === "warning" ? 72 : 38;
}

function showDialog(title, html) {
  let dialog = $("#appDialog");
  if (!dialog) {
    dialog = document.createElement("div");
    dialog.id = "appDialog";
    dialog.className = "dialog-backdrop";
    document.body.appendChild(dialog);
  }
  dialog.innerHTML = `
    <div class="dialog">
      <div class="dialog-head">
        <h3>${escapeHtml(title)}</h3>
        <button class="icon-mini" id="dialogClose" type="button"><i data-lucide="x"></i></button>
      </div>
      <div class="dialog-body">${html}</div>
    </div>
  `;
  dialog.classList.add("open");
  $("#dialogClose").addEventListener("click", closeDialog);
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) closeDialog();
  }, { once: true });
  refreshIcons();
}

function closeDialog() {
  const dialog = $("#appDialog");
  if (dialog) dialog.classList.remove("open");
}

function showCaseDetail(id) {
  const item = appData.cases.find((entry) => entry.id === id);
  if (!item) return;
  showDialog(item.title, `
    <img class="dialog-image" src="${escapeAttr(item.image)}" alt="${escapeAttr(item.title)}">
    <p>${escapeHtml(item.patient)}</p>
    <p>${escapeHtml(item.scenario)}</p>
    <div class="detail-list">
      <strong>预期意图</strong><span>${escapeHtml((item.expected_intent || item.tags || []).join("、"))}</span>
      <strong>预期动作</strong><span>${escapeHtml((item.expected_actions || []).join("、") || "发起对话后展示动作追踪")}</span>
      <strong>演示问题</strong><span>${escapeHtml(item.prompt)}</span>
    </div>
    <button class="primary-btn dialog-send" type="button"><i data-lucide="send-horizontal"></i><span>发起对话</span></button>
  `);
  $(".dialog-send").addEventListener("click", () => {
    closeDialog();
    sendMessage(item.prompt);
  });
  refreshIcons();
}

function showKnowledgeDetail(id) {
  const item = appData.knowledge.find((entry) => entry.id === id);
  if (!item) return;
  showDialog(item.title, `
    <img class="dialog-image" src="${escapeAttr(item.image)}" alt="${escapeAttr(item.title)}">
    <p>${escapeHtml(item.content)}</p>
    <div class="detail-list">
      <strong>红旗信号</strong><span>${escapeHtml((item.red_flags || []).join("、") || "暂无")}</span>
      <strong>记录字段</strong><span>${escapeHtml((item.record_fields || []).join("、") || "暂无")}</span>
      <strong>何时就医</strong><span>${escapeHtml(item.when_to_seek_care || "按症状变化及时就医")}</span>
      <strong>来源</strong><span>${escapeHtml(item.source || "结构化知识库")}</span>
    </div>
    <button class="primary-btn dialog-ask" type="button"><i data-lucide="message-circle"></i><span>追问这个知识</span></button>
  `);
  $(".dialog-ask").addEventListener("click", () => {
    closeDialog();
    sendMessage(`${item.title} 是什么意思？需要记录什么，什么时候就医？`);
  });
  refreshIcons();
}

function renderDemoRoutes() {
  const grid = $("#demoGrid");
  if (!grid) return;
  grid.innerHTML = `
    <article class="interactive-panel">
      <div class="panel-title-row">
        <h3>演示控制</h3>
        <button class="mini-secondary" id="resetDemoRouteBtn" type="button"><i data-lucide="rotate-ccw"></i><span>重置演示数据</span></button>
      </div>
      <p>重置会清空健康记录、提醒和动作日志，保留病例库、知识库和页面配置，方便重新答辩演示。</p>
    </article>
    ${demoRoutes.map((item) => `
    <article class="demo-card">
      <img src="${escapeAttr(item.image)}" alt="${escapeAttr(item.title)}">
      <div>
        <div class="meta-row"><span class="tag">${escapeHtml(item.expectedIntent)}</span></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.prompt)}</p>
        <div class="detail-list compact">
          <strong>预期写入</strong><span>${item.writes.map(escapeHtml).join("、")}</span>
          <strong>预期动作</strong><span>${item.actions.map(escapeHtml).join("、")}</span>
        </div>
        <div class="card-actions">
          <button class="mini-primary start-demo" type="button" data-prompt="${escapeAttr(item.prompt)}"><i data-lucide="play"></i><span>一键开始</span></button>
          <button class="mini-secondary copy-demo" type="button" data-prompt="${escapeAttr(item.prompt)}"><i data-lucide="copy"></i><span>复制脚本</span></button>
        </div>
      </div>
    </article>
  `).join("")}`;
  $("#resetDemoRouteBtn").addEventListener("click", async () => {
    await resetDemoData();
    await refreshRuntimeData();
    showToast("演示路线已重置");
  });
  $$(".start-demo").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));
  $$(".copy-demo").forEach((button) => button.addEventListener("click", async () => {
    await copyText(button.dataset.prompt);
    showToast("演示脚本已复制");
  }));
  refreshIcons();
}

function formatMessage(text) {
  const lines = escapeHtml(text || "").split("\n");
  let html = "";
  let listType = "";
  const closeList = () => {
    if (listType) {
      html += `</${listType}>`;
      listType = "";
    }
  };
  const inline = (value) => value
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  for (const line of lines) {
    const trimmed = line.trim();
    const heading = trimmed.match(/^#{1,4}\s+(.*)/);
    const numbered = trimmed.match(/^\d+\.\s+(.*)/);
    const bullet = trimmed.match(/^[-*]\s+(.*)/);
    if (heading) {
      closeList();
      html += `<h3>${inline(heading[1])}</h3>`;
      continue;
    }
    if (numbered) {
      if (listType !== "ol") {
        closeList();
        html += "<ol>";
        listType = "ol";
      }
      html += `<li>${inline(numbered[1])}</li>`;
      continue;
    }
    if (bullet) {
      if (listType !== "ul") {
        closeList();
        html += "<ul>";
        listType = "ul";
      }
      html += `<li>${inline(bullet[1])}</li>`;
      continue;
    }
    closeList();
    if (trimmed) html += `<p>${inline(trimmed)}</p>`;
  }
  closeList();
  return html || "<p></p>";
}

function openSuggestions() {
  $("#suggestionPanel").classList.add("open");
}

function closeSuggestions() {
  $("#suggestionPanel").classList.remove("open");
}

function showToast(message) {
  let wrap = $("#toastStack");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "toastStack";
    wrap.className = "toast-stack";
    document.body.appendChild(wrap);
  }
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<i data-lucide="check-circle-2"></i><span>${escapeHtml(message)}</span>`;
  wrap.appendChild(toast);
  refreshIcons();
  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 240);
  }, 2200);
}

function resizeInput() {
  const input = $("#messageInput");
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 138)}px`;
}

async function copyText(text) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(text);
    return;
  }
  $("#messageInput").value = text;
  $("#sendBtn").disabled = false;
}

function priorityLabel(priority) {
  return { high: "重要", medium: "普通", low: "低优先" }[priority] || "普通";
}

function routeLabel(route) {
  return { ACTION: "执行", HYBRID: "混合", RAG: "检索", SAFE: "安全" }[route] || route;
}

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("\n", " ");
}

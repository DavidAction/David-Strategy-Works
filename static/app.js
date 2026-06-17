const state = {
  company: null,
  profiles: [],
  activeProfileId: "",
  template: null,
  documentInsights: null,
  templateGuidance: null,
  plan: null,
  aiSettings: null,
  versions: [],
  currentVersionId: "",
  versionExports: {},
  grantDataset: null,
};

const emptyCompany = {
  basic: {
    name: "",
    ceo: "",
    founded: "",
    location: "",
    industry: "",
    website: "",
    contact: "",
  },
  legal: {
    businessNumber: "",
    corporateNumber: "",
    businessType: "",
    businessItem: "",
    capital: "",
    registryOffice: "",
    registrationStatus: "",
  },
  business: {
    oneLine: "",
    problem: "",
    solution: "",
    product: "",
    targetCustomer: "",
    stage: "",
    differentiation: "",
    revenueModel: "",
  },
  market: {
    marketSize: "",
    trend: "",
    competitors: "",
    positioning: "",
    goToMarket: "",
  },
  traction: {
    metrics: "",
    customers: "",
    partnerships: "",
    ip: "",
    certifications: "",
    pilotResults: "",
  },
  team: {
    founder: "",
    members: "",
    advisors: "",
    hiringPlan: "",
  },
  finance: {
    fundingNeed: "",
    useOfFunds: "",
    salesPlan: "",
    costPlan: "",
    milestones: "",
  },
  impact: {
    jobCreation: "",
    socialValue: "",
    regionalImpact: "",
    sustainability: "",
  },
  knowledge: {
    additionalNotes: "",
  },
};

const groups = [
  {
    key: "basic",
    title: "기본 정보",
    fields: [
      ["name", "회사명", "예: 브리웰"],
      ["ceo", "대표자", "대표자명"],
      ["founded", "설립일", "YYYY-MM-DD"],
      ["location", "소재지", "본점 또는 사업장 주소"],
      ["industry", "업종", "예: 헬스케어, 교육, SaaS"],
      ["website", "웹사이트", "https://"],
      ["contact", "연락처", "email@example.com"],
    ],
  },
  {
    key: "legal",
    title: "법적 정보",
    fields: [
      ["businessNumber", "사업자등록번호", "000-00-00000"],
      ["corporateNumber", "법인등록번호", "000000-0000000"],
      ["businessType", "업태", "서비스업"],
      ["businessItem", "종목", "소프트웨어 개발 및 공급"],
      ["capital", "자본금", "예: 10,000,000원"],
      ["registryOffice", "등기 관할", "관할등기소"],
      ["registrationStatus", "등록 상태", "계속사업자, 법인 등"],
    ],
  },
  {
    key: "business",
    title: "사업 아이덴티티",
    fields: [
      ["oneLine", "한 줄 소개", "고객과 제공가치를 한 문장으로"],
      ["problem", "고객 문제", "목표 고객이 반복적으로 겪는 불편"],
      ["solution", "해결 방식", "회사가 문제를 해결하는 방식"],
      ["product", "제품·서비스", "앱, 플랫폼, 프로그램, 디바이스 등"],
      ["targetCustomer", "목표 고객", "초기 고객군과 구매자"],
      ["stage", "현재 단계", "아이디어, MVP, 베타, 출시 등"],
      ["differentiation", "차별성", "경쟁사 대비 강점"],
      ["revenueModel", "수익모델", "구독, B2B 계약, 수수료 등"],
    ],
  },
  {
    key: "market",
    title: "시장과 경쟁",
    fields: [
      ["marketSize", "시장 규모", "TAM/SAM/SOM 또는 근거 자료"],
      ["trend", "시장 트렌드", "정책, 소비 변화, 기술 변화"],
      ["competitors", "경쟁사·대체재", "직접 경쟁사와 기존 대안"],
      ["positioning", "포지셔닝", "어떤 축에서 다르게 보일지"],
      ["goToMarket", "고객 확보 전략", "초기 채널과 세일즈 방식"],
    ],
  },
  {
    key: "traction",
    title: "검증과 성과",
    fields: [
      ["metrics", "검증 지표", "가입자, 인터뷰, 구매의향, 매출 등"],
      ["customers", "고객·파트너", "파일럿, LOI, 계약 등"],
      ["partnerships", "협력 현황", "기관, 기업, 커뮤니티 등"],
      ["ip", "지식재산", "특허, 상표, 저작권, 인허가"],
      ["certifications", "인증·허가", "필요 인증과 진행 상태"],
      ["pilotResults", "실증 결과", "테스트 결과와 인사이트"],
    ],
  },
  {
    key: "team",
    title: "팀 역량",
    fields: [
      ["founder", "대표 역량", "관련 경력, 창업 동기, 전문성"],
      ["members", "팀 구성", "역할별 담당자와 강점"],
      ["advisors", "멘토·자문", "외부 전문가와 협력망"],
      ["hiringPlan", "채용 계획", "지원 이후 보강할 인력"],
    ],
  },
  {
    key: "finance",
    title: "재무와 실행",
    fields: [
      ["fundingNeed", "필요 자금", "총 필요 자금과 근거"],
      ["useOfFunds", "자금 사용 계획", "개발, 마케팅, 인증, 인건비 등"],
      ["salesPlan", "매출 계획", "월별/분기별 매출 가정"],
      ["costPlan", "비용 계획", "고정비와 변동비"],
      ["milestones", "추진 일정", "지원기간 내 마일스톤"],
    ],
  },
  {
    key: "impact",
    title: "기대 효과",
    fields: [
      ["jobCreation", "고용 창출", "채용 인원과 시점"],
      ["socialValue", "사회적 가치", "고객 편익과 공공성"],
      ["regionalImpact", "지역 파급효과", "지역 기반 효과"],
      ["sustainability", "지속가능성", "장기 운영 계획"],
    ],
  },
];

const wideFields = new Set([
  "location",
  "businessItem",
  "problem",
  "solution",
  "product",
  "differentiation",
  "marketSize",
  "trend",
  "competitors",
  "goToMarket",
  "metrics",
  "customers",
  "partnerships",
  "founder",
  "members",
  "useOfFunds",
  "salesPlan",
  "milestones",
  "socialValue",
]);

function qs(selector) {
  return document.querySelector(selector);
}

function setStatus(message) {
  const node = qs("#saveStatus");
  if (node) node.textContent = message;
}

async function api(path, options = {}) {
  const workspacePassword = localStorage.getItem("dswWorkspacePassword") || "";
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (workspacePassword) headers["X-DSW-Workspace-Password"] = workspacePassword;
  const response = await fetch(path, {
    ...options,
    headers,
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (response.status === 401 && data.code === "workspace_password_required") {
    const password = window.prompt("워크스페이스 비밀번호를 입력하세요.");
    if (password) {
      localStorage.setItem("dswWorkspacePassword", password);
      return api(path, options);
    }
  }
  if (!response.ok) {
    throw new Error(data.error || "요청 처리 중 오류가 발생했습니다.");
  }
  return data;
}

async function downloadUrl(url) {
  const workspacePassword = localStorage.getItem("dswWorkspacePassword") || "";
  const headers = workspacePassword ? { "X-DSW-Workspace-Password": workspacePassword } : {};
  const response = await fetch(url, { headers });
  if (response.status === 401) {
    const password = window.prompt("워크스페이스 비밀번호를 입력하세요.");
    if (password) {
      localStorage.setItem("dswWorkspacePassword", password);
      return downloadUrl(url);
    }
  }
  if (!response.ok) throw new Error("파일을 다운로드할 수 없습니다.");
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = decodeURIComponent(url.split("/").pop() || "download");
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

function bindDownloadButtons(root = document) {
  root.querySelectorAll("[data-download-url]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await downloadUrl(button.dataset.downloadUrl);
      } catch (error) {
        setStatus(error.message || "파일 다운로드 중 오류가 발생했습니다.");
      }
    });
  });
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeCompany(company) {
  return mergeDeep(clone(emptyCompany), company || {});
}

function mergeDeep(base, patch, fillOnly = false) {
  const output = clone(base);
  Object.entries(patch || {}).forEach(([key, value]) => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      output[key] = mergeDeep(output[key] || {}, value, fillOnly);
    } else if (!fillOnly || !String(output[key] || "").trim()) {
      output[key] = value;
    }
  });
  return output;
}

function renderCompanyForm() {
  const root = qs("#companyForm");
  root.innerHTML = "";
  groups.forEach((group) => {
    const section = document.createElement("section");
    section.className = "field-group";
    section.innerHTML = `<h3>${group.title}</h3><div class="fields"></div>`;
    const fieldsRoot = section.querySelector(".fields");
    group.fields.forEach(([key, label, placeholder]) => {
      const id = `${group.key}.${key}`;
      const current = state.company?.[group.key]?.[key] || "";
      const isWide = wideFields.has(key);
      const input = isWide
        ? `<textarea id="${id}" data-group="${group.key}" data-key="${key}" rows="3" placeholder="${escapeAttr(placeholder)}">${escapeHtml(current)}</textarea>`
        : `<input id="${id}" data-group="${group.key}" data-key="${key}" value="${escapeAttr(current)}" placeholder="${escapeAttr(placeholder)}" />`;
      const field = document.createElement("div");
      field.className = `field ${isWide ? "wide" : ""}`;
      field.innerHTML = `<label for="${id}">${label}</label>${input}`;
      fieldsRoot.appendChild(field);
    });
    root.appendChild(section);
  });
  syncAuxInputs();
  renderMetrics();
}

function collectCompany() {
  const company = clone(emptyCompany);
  groups.forEach((group) => {
    group.fields.forEach(([key]) => {
      const node = document.querySelector(`[data-group="${group.key}"][data-key="${key}"]`);
      company[group.key][key] = node?.value.trim() || "";
    });
  });
  company.knowledge.additionalNotes = qs("#additionalNotes")?.value.trim() || "";
  return company;
}

function collectCompanySafe() {
  try {
    return collectCompany();
  } catch {
    return state.company || emptyCompany;
  }
}

function syncAuxInputs() {
  const notes = qs("#additionalNotes");
  if (notes && state.company?.knowledge?.additionalNotes && !notes.value) {
    notes.value = state.company.knowledge.additionalNotes;
  }
}

function renderProfileSelect() {
  const select = qs("#profileSelect");
  if (!select) return;
  const options = [
    `<option value="__new"${state.activeProfileId ? "" : " selected"}>새 회사 프로필 작성</option>`,
    ...state.profiles.map(
      (profile) =>
        `<option value="${escapeAttr(profile.id)}"${profile.id === state.activeProfileId ? " selected" : ""}>${escapeHtml(profile.name || "미입력 회사")}</option>`
    ),
  ];
  select.innerHTML = options.join("");
}

async function loadProfiles() {
  const result = await api("/api/profiles");
  state.profiles = result.profiles || [];
  state.activeProfileId = result.activeProfileId || "";
  renderProfileSelect();
  return result;
}

async function loadAiSettings() {
  state.aiSettings = await api("/api/ai/settings");
  renderAiEngine();
}

async function loadGrantDataset() {
  try {
    state.grantDataset = await api("/api/grant-dataset");
  } catch {
    state.grantDataset = null;
  }
}

function currentWorkspacePayload() {
  return {
    company: collectCompany(),
    documentInsights: state.documentInsights,
    template: state.template,
    templateGuidance: collectTemplateGuidance(),
    plan: state.plan,
    grantName: qs("#grantName")?.value.trim() || "",
    lengthMode: qs("#lengthMode")?.value || "balanced",
  };
}

async function loadProfile(profileId) {
  if (!profileId || profileId === "__new") {
    resetWorkspaceForProfile();
    state.activeProfileId = "";
    renderProfileSelect();
    await loadVersions();
    setStatus("새 회사 프로필 작성 중");
    return;
  }
  setStatus("프로필 불러오는 중");
  const profile = await api(`/api/profiles/${encodeURIComponent(profileId)}`);
  const workspace = profile.workspace || {};
  state.activeProfileId = profile.id;
  state.company = normalizeCompany(workspace.company || profile.company || {});
  state.documentInsights = workspace.documentInsights || null;
  state.template = workspace.template || null;
  state.templateGuidance = workspace.templateGuidance || null;
  state.plan = workspace.plan || null;
  state.currentVersionId = "";
  state.versionExports = {};
  renderCompanyForm();
  restoreWorkspaceInputs(workspace);
  renderProfileSelect();
  renderDocumentInsights();
  renderAnalysis();
  renderDraft();
  await loadVersions();
  setStatus(`${profile.name || "회사"} 프로필 불러오기 완료`);
}

function restoreWorkspaceInputs(workspace) {
  qs("#additionalNotes").value = state.company?.knowledge?.additionalNotes || "";
  qs("#grantName").value = workspace.grantName || state.plan?.grantName || "";
  qs("#lengthMode").value = workspace.lengthMode || "balanced";
  const guidance = state.templateGuidance || {};
  qs("#targetPages").value = guidance.pageCount || "";
  qs("#structureBrief").value = guidance.structure || "";
  qs("#focusBrief").value = guidance.focusPoints || "";
  qs("#formatRules").value = guidance.formatRules || "";
  qs("#templateComments").value = guidance.comments || "";
  qs("#strictFormat").checked = guidance.strictFormat !== false;
}

async function saveCompany() {
  state.company = collectCompany();
  setStatus("저장 중");
  const result = await api("/api/profiles", {
    method: "POST",
    body: JSON.stringify({
      profileId: state.activeProfileId || "",
      company: state.company,
      workspace: currentWorkspacePayload(),
    }),
  });
  state.profiles = result.profiles || [];
  state.activeProfileId = result.activeProfileId || result.profile?.id || "";
  state.company = normalizeCompany(result.profile?.company || state.company);
  renderCompanyForm();
  renderProfileSelect();
  await loadVersions();
  setStatus("프로필 저장 완료");
}

function resetWorkspaceForProfile() {
  state.company = normalizeCompany({});
  state.template = null;
  state.documentInsights = null;
  state.templateGuidance = null;
  state.plan = null;
  state.versions = [];
  state.currentVersionId = "";
  state.versionExports = {};
  qs("#companyDocs").value = "";
  qs("#documentText").value = "";
  qs("#additionalNotes").value = "";
  qs("#templateFile").value = "";
  qs("#templateText").value = "";
  qs("#targetPages").value = "";
  qs("#structureBrief").value = "";
  qs("#focusBrief").value = "";
  qs("#formatRules").value = "";
  qs("#templateComments").value = "";
  qs("#strictFormat").checked = true;
  qs("#grantName").value = "";
  qs("#versionLabel").value = "";
  qs("#revisionComments").value = "";
  renderCompanyForm();
  renderDocumentInsights();
  renderAnalysis();
  renderDraft();
  renderExports(null);
  renderVersionSelect();
  activatePanel("profile");
}

function collectTemplateGuidance() {
  return {
    pageCount: qs("#targetPages")?.value.trim() || "",
    structure: qs("#structureBrief")?.value.trim() || "",
    focusPoints: qs("#focusBrief")?.value.trim() || "",
    formatRules: qs("#formatRules")?.value.trim() || "",
    comments: qs("#templateComments")?.value.trim() || "",
    strictFormat: Boolean(qs("#strictFormat")?.checked),
  };
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    if (!file) return resolve("");
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function analyzeDocuments() {
  const files = Array.from(qs("#companyDocs").files || []);
  const pasted = qs("#documentText").value.trim();
  const notes = qs("#additionalNotes").value.trim();
  if (!files.length && !pasted && !notes) {
    setStatus("회사 문서 또는 추가 의견이 필요합니다.");
    return;
  }

  setStatus("회사 문서 분석 중");
  const typeHint = qs("#documentTypeHint").value;
  const documents = [];
  for (const file of files) {
    documents.push({
      filename: file.name,
      contentBase64: await fileToBase64(file),
      documentType: typeHint,
    });
  }
  if (pasted) {
    documents.push({
      filename: "manual-company-context.txt",
      contentBase64: "",
      documentType: typeHint || "general",
      text: pasted,
    });
  }

  state.documentInsights = await api("/api/documents/analyze", {
    method: "POST",
    body: JSON.stringify({ documents, notes }),
  });
  state.company = mergeDeep(collectCompany(), state.documentInsights.companyPatch || {}, true);
  renderCompanyForm();
  renderDocumentInsights();
  activatePanel("documents");
  setStatus("회사 문서 분석 완료");
}

function applyDocumentPatch() {
  if (!state.documentInsights?.companyPatch) {
    setStatus("반영할 분석 결과가 없습니다.");
    return;
  }
  state.company = mergeDeep(collectCompany(), state.documentInsights.companyPatch, true);
  renderCompanyForm();
  setStatus("분석 결과 반영 완료");
}

function renderDocumentInsights() {
  const insights = state.documentInsights;
  qs("#documentCount").textContent = insights?.documents?.length || 0;
  qs("#factCount").textContent = insights?.facts?.length || 0;
  qs("#patchCount").textContent = countPatch(insights?.companyPatch || {});
  const root = qs("#documentResults");
  const factsRoot = qs("#factResults");
  const summaryRoot = qs("#documentSummary");
  if (!insights) {
    if (summaryRoot) {
      summaryRoot.className = "document-summary empty-state";
      summaryRoot.textContent = "문서가 많아지면 핵심 근거와 부족한 증빙 영역을 자동으로 정리합니다.";
    }
    root.className = "list-stack empty-state";
    root.textContent = "분석된 회사 문서가 없습니다.";
    factsRoot.innerHTML = "";
    renderMetrics();
    return;
  }

  renderDocumentLibrarySummary(insights.librarySummary, insights.businessUnderstanding);
  root.className = "list-stack";
  root.innerHTML = [...(insights.documents || [])]
    .sort((a, b) => Number(b.relevanceScore || 0) - Number(a.relevanceScore || 0))
    .map((doc) => {
      const ocr = doc.ocrStatus || {};
      const notes = (doc.notes || []).map((note) => `<p class="micro">${escapeHtml(note)}</p>`).join("");
      const coverage = (doc.coverageTags || [])
        .map((tag) => `<span title="${escapeAttr(`${tag.keywordHits || 0} keyword hits`)}">${escapeHtml(tag.label)}</span>`)
        .join("");
      const snippets = (doc.evidenceSnippets || [])
        .slice(0, 4)
        .map(
          (snippet) => `
            <li>
              <span>${escapeHtml(snippet.categoryLabel || "근거")}</span>
              <p>${escapeHtml(snippet.text || "")}</p>
            </li>
          `
        )
        .join("");
      return `
        <article class="insight-item document-insight ${escapeAttr(doc.priority || "low")}">
          <div class="item-title">
            <span class="tag">${escapeHtml(doc.documentTypeLabel || "문서")}</span>
            <strong>${escapeHtml(doc.filename)}</strong>
            <span class="document-score">${Number(doc.relevanceScore || 0)}점</span>
            <span class="quality-badge ${escapeAttr(doc.extractionQuality?.status || "")}">${escapeHtml(qualityLabel(doc.extractionQuality))}</span>
            ${doc.duplicateOf ? `<span class="ocr-badge needs_ocr">중복: ${escapeHtml(doc.duplicateOf)}</span>` : ""}
            ${ocr.status ? `<span class="ocr-badge ${escapeAttr(ocr.status)}">${escapeHtml(ocrLabel(ocr))}</span>` : ""}
          </div>
          <p class="hint">${escapeHtml(doc.summary || "")}</p>
          <p class="micro">${priorityLabel(doc.priority)} · ${Number(doc.extractedCharacters || 0).toLocaleString()}자 추출 · ${Number(doc.byteSize || 0).toLocaleString()} bytes · ${escapeHtml(completenessLabel(doc.extractionCompleteness))}</p>
          <p class="hint">${escapeHtml(doc.recommendedUse || "")}</p>
          ${coverage ? `<div class="coverage-chips">${coverage}</div>` : ""}
          ${snippets ? `<ol class="evidence-snippets">${snippets}</ol>` : ""}
          ${notes}
        </article>
      `;
    })
    .join("");

  factsRoot.innerHTML = (insights.facts || [])
    .slice(0, 12)
    .map(
      (fact) => `
        <article class="fact-item">
          <span>${escapeHtml(fact.label)}</span>
          <strong>${escapeHtml(fact.value)}</strong>
        </article>
      `
    )
    .join("");
  renderMetrics();
}

function renderDocumentLibrarySummary(summary, understanding = null) {
  const root = qs("#documentSummary");
  if (!root) return;
  if (!summary) {
    root.className = "document-summary empty-state";
    root.textContent = "문서 요약이 없습니다.";
    return;
  }
  root.className = "document-summary";
  const coverage = (summary.coverage || [])
    .map(
      (item) => `
        <article class="coverage-item ${escapeAttr(item.status || "")}">
          <span>${escapeHtml(item.label)}</span>
          <strong>${Number(item.documentCount || 0)}</strong>
          <small>${Number(item.snippetCount || 0)}개 증빙</small>
        </article>
      `
    )
    .join("");
  const highValue = (summary.highValueDocuments || [])
    .slice(0, 5)
    .map((item) => `<li>${escapeHtml(item.filename)} <strong>${Number(item.score || 0)}점</strong></li>`)
    .join("");
  const actions = (summary.recommendedActions || []).map((action) => `<li>${escapeHtml(action)}</li>`).join("");
  const warnings = (summary.warnings || [])
    .map((warning) => `<li>${escapeHtml(warning.filename)}: ${escapeHtml(warning.message)}</li>`)
    .join("");
  root.innerHTML = `
    <article class="document-summary-hero">
      <span>근거자료 라이브러리 분석</span>
      <strong>${Number(summary.totalDocuments || 0)}개 문서 · ${Number(summary.totalEvidenceSnippets || 0)}개 핵심 증빙 · ${Number(summary.totalFacts || 0)}개 사실</strong>
      <p>${Number(summary.totalCharacters || 0).toLocaleString()}자 추출. 점수가 높은 문서와 부족한 근거 영역을 기준으로 초안 생성에 반영합니다.</p>
    </article>
    ${renderBusinessUnderstandingPanel(understanding)}
    <div class="coverage-grid">${coverage}</div>
    <div class="document-summary-columns">
      <section>
        <h4>우선 활용 문서</h4>
        <ul>${highValue || "<li>아직 우선 문서가 없습니다.</li>"}</ul>
      </section>
      <section>
        <h4>권장 보강</h4>
        <ul>${actions || "<li>권장 보강 사항이 없습니다.</li>"}</ul>
      </section>
      ${warnings ? `<section><h4>확인 필요</h4><ul>${warnings}</ul></section>` : ""}
    </div>
  `;
}

function renderBusinessUnderstandingPanel(understanding) {
  if (!understanding) return "";
  const completeness = understanding.extractionCompleteness || {};
  const coverage = (understanding.coverage || [])
    .map(
      (item) => `
        <article class="understanding-coverage ${escapeAttr(item.status || "")}">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(understandingStatusLabel(item.status))}</strong>
          <small>${Number(item.evidenceCount || 0)}개 근거 · 신뢰도 ${Number(item.confidence || 0)}점</small>
        </article>
      `
    )
    .join("");
  const evidence = (understanding.evidenceBank || [])
    .slice(0, 8)
    .map(
      (item) => `
        <li>
          <span>${escapeHtml(item.areaLabel || "사업 근거")} · ${escapeHtml(item.source || "")}</span>
          <p>${escapeHtml(item.text || "")}</p>
        </li>
      `
    )
    .join("");
  const missing = (understanding.missingCriticalDetails || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  const warnings = (completeness.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  return `
    <section class="business-understanding-panel">
      <div class="business-understanding-head">
        <span>기존 사업계획서 심층 이해</span>
        <strong>${Number(completeness.totalExtractedCharacters || 0).toLocaleString()}자 원문 기반 · 완료 ${Number(completeness.completeDocuments || 0)}건 · 보완 ${Number(completeness.partialDocuments || 0)}건 · 차단 ${Number(completeness.blockedDocuments || 0)}건</strong>
        <p>업로드한 기존 사업계획서를 문제, 고객, 솔루션, 시장, 사업화, 예산, 팀, 일정 단위로 재구성해 새 양식 작성 근거로 사용합니다.</p>
      </div>
      <div class="understanding-grid">${coverage}</div>
      ${evidence ? `<ol class="understanding-evidence">${evidence}</ol>` : ""}
      ${missing ? `<div class="missing-detail-chips"><strong>보완 필요</strong>${missing}</div>` : ""}
      ${warnings ? `<div class="understanding-warnings"><strong>원문 추출 확인</strong><ul>${warnings}</ul></div>` : ""}
    </section>
  `;
}

function ocrLabel(ocr) {
  if (ocr.status === "completed_or_text_available") return "OCR/텍스트 확보";
  if (ocr.status === "needs_ocr") return "OCR 필요";
  return "텍스트 추출";
}

function completenessLabel(completeness) {
  const labels = {
    complete: "원문 추출 완료",
    partial: "원문 일부 확인 필요",
    weak: "원문 보강 필요",
    blocked: "OCR/원문 입력 필요",
  };
  return labels[completeness?.status] || "원문 추출 확인";
}

function understandingStatusLabel(status) {
  const labels = {
    strong: "충분",
    partial: "부분",
    missing: "부족",
  };
  return labels[status] || "확인";
}

function priorityLabel(priority) {
  const labels = {
    high: "핵심 근거",
    medium: "보조 근거",
    low: "참고 문서",
    needs_review: "추출 확인 필요",
    duplicate: "중복 문서",
  };
  return labels[priority] || "참고 문서";
}

function qualityLabel(quality = {}) {
  if (quality.status === "strong") return `추출 우수 ${quality.score || 0}점`;
  if (quality.status === "partial") return `부분 추출 ${quality.score || 0}점`;
  if (quality.status === "weak") return `추출 취약 ${quality.score || 0}점`;
  return "추출 품질";
}

async function analyzeTemplate() {
  const file = qs("#templateFile").files[0];
  const text = qs("#templateText").value;
  if (!file && !text.trim()) {
    setStatus("양식 파일 또는 텍스트가 필요합니다.");
    return;
  }
  setStatus("지원사업 양식 분석 중");
  state.template = await api("/api/analyze", {
    method: "POST",
    body: JSON.stringify({
      filename: file?.name || "pasted-template.txt",
      contentBase64: await fileToBase64(file),
      text,
    }),
  });
  state.templateGuidance = collectTemplateGuidance();
  qs("#grantName").value = state.template.title || "";
  renderAnalysis();
  activatePanel("draft");
  setStatus("양식 분석 완료");
}

function renderAnalysis() {
  const template = state.template;
  qs("#questionCount").textContent = template?.questions?.length || 0;
  qs("#charCount").textContent = template?.extractedCharacters || 0;
  qs("#keywordCount").textContent = template?.keywords?.length || 0;
  const root = qs("#analysisResults");
  if (!template) {
    root.className = "list-stack empty-state";
    root.textContent = "분석된 지원사업 양식이 없습니다.";
    renderMetrics();
    return;
  }
  root.className = "list-stack";
  const notes = (template.notes || []).map((note) => `<p class="hint">${escapeHtml(note)}</p>`).join("");
  const source = renderTemplateSource(template.templateSource);
  const criteria = renderSuccessCriteria(template.successCriteria);
  const requirements = (template.requirements || [])
    .map(
      (req) => `
        <article class="insight-item requirement-item">
          <div class="item-title">
            <span class="tag">${escapeHtml(req.label || "요구사항")}</span>
            <strong>${escapeHtml(req.value || "")}</strong>
          </div>
          <p class="micro">${escapeHtml(req.source || "양식 자동 감지")}</p>
        </article>
      `
    )
    .join("");
  const items = (template.questions || [])
    .map(
      (q, index) => `
        <article class="insight-item">
          <div class="item-title">
            <span class="tag ${escapeAttr(q.category || "overview")}">${categoryLabel(q.category)}</span>
            <strong>${index + 1}. ${escapeHtml(q.prompt)}</strong>
          </div>
          <p class="hint">${escapeHtml(q.evaluationFocus || "")}</p>
          <p class="micro">${escapeHtml(q.answerStrategy || "")}</p>
        </article>
      `
    )
    .join("");
  root.innerHTML = source + criteria + notes + requirements + items;
  renderMetrics();
}

function renderTemplateSource(source = {}) {
  if (!source || source.mode === "none") return "";
  const mode = source.mode === "uploaded_file" ? "업로드 양식 보존" : "붙여넣은 양식 기록";
  const preservable = source.preservable ? "원본 제출양식 패키지 포함 가능" : "텍스트 기준 매핑 패키지 생성";
  return `
    <article class="insight-item template-source">
      <div class="item-title">
        <span class="tag">원본 양식</span>
        <strong>${escapeHtml(source.filename || source.storedName || "양식")}</strong>
      </div>
      <p class="hint">${mode} · ${preservable}</p>
      <p class="micro">저장명: ${escapeHtml(source.storedName || "-")} · ${Number(source.bytes || 0).toLocaleString()} bytes</p>
    </article>
  `;
}

function renderSuccessCriteria(criteria = {}) {
  if (!criteria || !criteria.name) return "";
  const weights = (criteria.scoringWeights || [])
    .map((item) => `<li><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.weight)}점</span></li>`)
    .join("");
  const patterns = (criteria.successPatterns || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const risks = (criteria.rejectionRisks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const evidence = (criteria.evidenceChecklist || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  return `
    <article class="criteria-card">
      <div>
        <span class="tag">선정 기준</span>
        <strong>${escapeHtml(criteria.name)}</strong>
        <p class="hint">양식과 공고 키워드를 기준으로 합격 가능성을 높이는 작성 기준을 연결했습니다.</p>
      </div>
      <div class="criteria-grid">
        <section>
          <h4>평가 배점</h4>
          <ul>${weights}</ul>
        </section>
        <section>
          <h4>합격 패턴</h4>
          <ul>${patterns}</ul>
        </section>
        <section>
          <h4>탈락 리스크</h4>
          <ul>${risks}</ul>
        </section>
      </div>
      <div class="evidence-chips">${evidence}</div>
    </article>
  `;
}

async function generateDraft() {
  state.company = collectCompany();
  state.templateGuidance = collectTemplateGuidance();
  setStatus("초안 생성 중");
  state.plan = await api("/api/generate", {
    method: "POST",
    body: JSON.stringify({
      company: state.company,
      template: state.template || {},
      documentInsights: state.documentInsights || {},
      additionalNotes: qs("#additionalNotes").value.trim(),
      options: {
        grantName: qs("#grantName").value.trim(),
        length: qs("#lengthMode").value,
        templateGuidance: state.templateGuidance,
        profileId: state.activeProfileId || "default-workspace",
        useAI: true,
      },
    }),
  });
  renderDraft();
  activatePanel("draft");
  await autoSaveDraftVersion(`${state.plan.grantName || "지원사업"} 최초 생성본`, "generated");
  setStatus("초안 생성 및 버전 저장 완료");
}

function renderDraft() {
  const plan = state.plan;
  const summary = qs("#draftSummary");
  const root = qs("#draftSections");
  if (!plan) {
    summary.textContent = "회사 프로필, 회사 문서, 지원사업 양식을 준비한 뒤 초안을 생성하세요.";
    root.innerHTML = "";
    renderAiEngine();
    renderScorecard();
    renderValidation();
    renderOperationalReports();
    renderEvidenceTraceability();
    renderUnsupportedClaimAudit();
    renderVisualAssets();
    renderQuality();
    renderMetrics();
    return;
  }
  summary.textContent = plan.summary || "초안이 생성되었습니다.";
  renderAiEngine();
  renderScorecard();
  renderValidation();
  renderOperationalReports();
  renderEvidenceTraceability();
  renderUnsupportedClaimAudit();
  renderVisualAssets();
  root.innerHTML = (plan.sections || [])
    .map(
      (section, index) => `
        <article class="draft-card" data-section="${escapeAttr(section.id || `s${index}`)}">
          <header>
            <div>
              <div class="item-title">
                <span class="tag ${escapeAttr(section.category || "overview")}">${categoryLabel(section.category)}</span>
                <h3>${index + 1}. ${escapeHtml(section.heading || "사업계획 항목")}</h3>
              </div>
              <p class="hint">${escapeHtml(section.evaluationFocus || "")}</p>
            </div>
          </header>
          <textarea data-draft="${escapeAttr(section.id || `s${index}`)}" rows="9">${escapeHtml(section.content || "")}</textarea>
          <div class="advisory-note">
            <strong>작성 전략</strong>
            <span>${escapeHtml(section.answerStrategy || "")}</span>
          </div>
          <p class="micro">증빙자료: ${escapeHtml((section.evidenceNeeded || []).join(", "))}</p>
        </article>
      `
    )
    .join("");
  root.querySelectorAll("[data-draft]").forEach((textarea) => {
    textarea.addEventListener("input", () => {
      const section = state.plan.sections.find((item) => String(item.id) === textarea.dataset.draft);
      if (section) section.content = textarea.value;
    });
  });
  renderQuality();
  renderMetrics();
}

function renderQuality() {
  const root = qs("#qualityChecks");
  const checks = state.plan?.qualityChecks || [];
  if (!checks.length) {
    root.innerHTML = "";
    return;
  }
  root.innerHTML = checks
    .map(
      (check) => `
        <article class="quality-item ${escapeAttr(check.status || "")}">
          <strong>${escapeHtml(check.label)}</strong>
          <p class="hint">${escapeHtml(check.message)}</p>
        </article>
      `
    )
    .join("");
}

function renderAiEngine() {
  const targets = [qs("#aiEnginePanel"), qs("#exportAiEnginePanel")].filter(Boolean);
  const settings = state.aiSettings;
  const engine = state.plan?.aiEngine;
  targets.forEach((root) => {
    if (!settings && !engine) {
      root.innerHTML = "";
      return;
    }
    const assignments = engine?.assignments || settings?.assignments || {};
    const configured = Boolean(engine?.apiKeyConfigured ?? settings?.configured);
    const mode = engine?.mode || (configured ? "multi_provider_ready" : "local_fallback");
    const statusText =
      engine?.message ||
      "API 키가 있으면 Gemini, GPT, Claude를 단계별로 사용하고, 키가 없으면 로컬 규칙 기반 초안 생성으로 동작합니다.";
    const modelLabel = (assignment, fallbackProvider, fallbackModel) => {
      const provider = assignment?.provider || fallbackProvider;
      const model = assignment?.model || assignment?.imageModel || fallbackModel;
      return `${provider} · ${model}`;
    };
    const cards = [
      ["한글 초안 작성", modelLabel(assignments.primaryDraft, "Google", "gemini-3.5-flash"), "한국어 사업계획서 1차 문장과 문항별 초안 생성"],
      ["제출 문장 정제", modelLabel(assignments.finalPolish, "OpenAI", "gpt-5.5"), "제출용 문체, 구조화 출력, 형식 검증 보강"],
      ["문서 분석", modelLabel(assignments.documentAnalysis, "Google", "gemini-3.1-flash-lite"), "업로드 문서 요약, 사실 추출, 회사 프로필 보강"],
      ["고급 초안 후보", modelLabel(assignments.firstDraftAlternative, "Google", "gemini-3.1-pro-preview"), "긴 자료와 복합 양식에 대한 대체 초안"],
      ["형식 검증", modelLabel(assignments.formatReview, "OpenAI", "gpt-5.5"), "분량, 문항 순서, 제출 규칙 점검"],
      ["최종 심사 리뷰", modelLabel(assignments.strategicRedTeam, "Anthropic", "claude-opus-4-8"), "심사위원 관점의 반박, 리스크, 논리 공백 검토"],
      ["시각자료 브리프", modelLabel(assignments.visualPlanning, "Google", "gemini-3-pro-image"), "표, 인포그래픽, 이미지 생성 지시문 설계"],
    ];
    const pipeline = (engine?.pipeline || [])
      .map(
        (item) => `
          <article class="ai-pipeline-step ${escapeAttr(item.status || "")}">
            <span>${escapeHtml(item.stage || "")}</span>
            <strong>${escapeHtml(`${item.provider || ""} ${item.model || ""}`.trim())}</strong>
            <small>${escapeHtml(item.status || "")}</small>
          </article>
        `
      )
      .join("");
    root.innerHTML = `
      <article class="ai-engine-hero ${configured ? "ready" : "fallback"}">
        <div>
          <span>AI 운영 엔진</span>
          <strong>${configured ? "멀티 모델 API 준비됨" : "로컬 생성 모드"}</strong>
          <p>${escapeHtml(statusText)}</p>
        </div>
        <em>${escapeHtml(mode)}</em>
      </article>
      ${cards
        .map(
          ([label, model, role]) => `
            <article class="ai-engine-card">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(model)}</strong>
              <p class="hint">${escapeHtml(role)}</p>
            </article>
          `
        )
        .join("")}
      ${pipeline ? `<article class="ai-pipeline-board"><span>실행 파이프라인</span><div>${pipeline}</div></article>` : ""}
    `;
  });
}

function renderVisualAssets() {
  const targets = [qs("#visualAssets"), qs("#exportVisualAssets")].filter(Boolean);
  const assets = state.plan?.visualAssets;
  targets.forEach((root) => {
    if (!assets) {
      root.innerHTML = "";
      return;
    }
    const tables = (assets.tables || []).map(renderTableAsset).join("");
    const graphics = (assets.infographics || []).map(renderInfographicAsset).join("");
    const imageBriefs = (assets.imageBriefs || []).map(renderImageBrief).join("");
    root.innerHTML = `
      <article class="visual-strategy">
        <span>시각자료 배치 전략</span>
        <strong>표 ${(assets.tables || []).length}개 · 인포그래픽 ${(assets.infographics || []).length}개 · 이미지 브리프 ${(assets.imageBriefs || []).length}개</strong>
        <p>${escapeHtml(assets.strategy || "")}</p>
      </article>
      ${tables}
      ${graphics}
      ${imageBriefs}
    `;
  });
}

function renderTableAsset(table) {
  const head = (table.columns || []).map((column) => `<th>${escapeHtml(column)}</th>`).join("");
  const rows = (table.rows || [])
    .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`)
    .join("");
  return `
    <article class="visual-card table-card">
      <div class="visual-card-head">
        <span>표</span>
        <strong>${escapeHtml(table.title || "표")}</strong>
        <small>${escapeHtml(table.placement || "")}</small>
      </div>
      <div class="table-scroll">
        <table>
          <thead><tr>${head}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </article>
  `;
}

function renderInfographicAsset(graphic) {
  const nodes = (graphic.nodes || [])
    .map(
      (node) => `
        <li>
          <strong>${escapeHtml(node.label || "")}</strong>
          <span>${escapeHtml(node.text || "")}</span>
        </li>
      `
    )
    .join("");
  return `
    <article class="visual-card infographic-card ${escapeAttr(graphic.type || "")}">
      <div class="visual-card-head">
        <span>인포그래픽</span>
        <strong>${escapeHtml(graphic.title || "인포그래픽")}</strong>
        <small>${escapeHtml(graphic.placement || "")}</small>
      </div>
      <ol>${nodes}</ol>
    </article>
  `;
}

function renderImageBrief(brief) {
  return `
    <article class="visual-card image-brief-card">
      <div class="visual-card-head">
        <span>이미지 브리프</span>
        <strong>${escapeHtml(brief.title || "이미지 생성 브리프")}</strong>
        <small>${escapeHtml(brief.placement || "")}</small>
      </div>
      <p class="hint">${escapeHtml(brief.prompt || "")}</p>
      <p class="micro">모델: ${escapeHtml(brief.model || "gemini-3-pro-image")}</p>
    </article>
  `;
}

function renderScorecard() {
  const targets = [qs("#proposalScorecard"), qs("#exportScorecard")].filter(Boolean);
  const scorecard = state.plan?.proposalScorecard;
  targets.forEach((root) => {
    if (!scorecard) {
      root.innerHTML = "";
      return;
    }
    const actions = (scorecard.priorityActions || []).map((action) => `<li>${escapeHtml(action)}</li>`).join("");
    const items = (scorecard.items || [])
      .map(
        (item) => `
          <article class="score-item ${escapeAttr(item.status || "")}">
            <span>${escapeHtml(item.label)}</span>
            <strong>${escapeHtml(item.score)} / ${escapeHtml(item.weight)}</strong>
            <p class="hint">${escapeHtml(item.action)}</p>
          </article>
        `
      )
      .join("");
    root.innerHTML = `
      <article class="score-hero">
        <span>심사 준비도</span>
        <strong>${escapeHtml(scorecard.score)}점</strong>
        <p>${escapeHtml(scorecard.readiness || "")}</p>
        <small>${escapeHtml(scorecard.message || "")}</small>
      </article>
      <article class="score-actions">
        <strong>우선 보완 액션</strong>
        <ul>${actions || "<li>현재 기준에서 큰 결함이 감지되지 않았습니다.</li>"}</ul>
      </article>
      ${items}
    `;
  });
}

function renderValidation() {
  const targets = [qs("#formatValidation"), qs("#exportValidation")].filter(Boolean);
  const validations = state.plan?.formatValidation || [];
  targets.forEach((root) => {
    if (!validations.length) {
      root.innerHTML = "";
      return;
    }
    root.innerHTML = validations
      .map(
        (item) => `
          <article class="validation-item ${escapeAttr(item.status || "")}">
            <strong>${escapeHtml(item.label)}</strong>
            <p class="hint">${escapeHtml(item.message)}</p>
          </article>
        `
      )
      .join("");
  });
}

function renderOperationalReports() {
  renderTemplateFillManifest();
  renderSubmissionFidelityReport();
  renderEvidenceLockReport();
  renderConsultantReview();
  renderJudgeReviewPack();
  renderSecurityReport();
  renderAiCostLedger();
  renderSecureTransferPolicy();
  renderWorkspaceManagement();
}

function renderTemplateFillManifest() {
  const targets = [qs("#templateFillManifest"), qs("#exportTemplateFillManifest")].filter(Boolean);
  const manifest = state.plan?.templateFillManifest;
  targets.forEach((root) => {
    if (!manifest) {
      root.innerHTML = "";
      return;
    }
    const rows = (manifest.rows || [])
      .slice(0, 6)
      .map((row) => `<li>${Number(row.order || 0)}. ${escapeHtml(row.templatePrompt || row.draftHeading || "")} <strong>${Number(row.answerCharacters || 0).toLocaleString()}자</strong></li>`)
      .join("");
    root.innerHTML = `
      <article class="ops-card ${escapeAttr(manifest.status || "")}">
        <span>HWPX 양식 기입 매핑</span>
        <strong>${manifest.exactCellFillReady ? "문항 단위 매핑 준비" : "수동 확인 필요"}</strong>
        <p>${escapeHtml(manifest.message || "")}</p>
        <ul>${rows}</ul>
      </article>
    `;
  });
}

function renderSubmissionFidelityReport() {
  const targets = [qs("#submissionFidelityReport"), qs("#exportSubmissionFidelityReport")].filter(Boolean);
  const report = state.plan?.submissionFidelityReport;
  targets.forEach((root) => {
    if (!report) {
      root.innerHTML = "";
      return;
    }
    const hwpx = report.hwpxAnalysis || {};
    const risks = (report.riskItems || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    root.innerHTML = `
      <article class="ops-card ${escapeAttr(report.status || "")}">
        <span>제출 양식 충실도</span>
        <strong>섹션 ${Number(hwpx.sectionXmlCount || 0)} · 표 ${Number(hwpx.tableCount || 0)} · 셀 ${Number(hwpx.cellCount || 0)}</strong>
        <p>${escapeHtml(report.nextAction || report.hwpxAnalysis?.message || "")}</p>
        <ul>${risks || `<li>매핑 답변 ${Number(report.mappedAnswerCount || 0)}개가 준비됐습니다.</li>`}</ul>
      </article>
    `;
  });
}

function renderEvidenceLockReport() {
  const targets = [qs("#evidenceLockReport"), qs("#exportEvidenceLockReport")].filter(Boolean);
  const report = state.plan?.evidenceLockReport;
  targets.forEach((root) => {
    if (!report) {
      root.innerHTML = "";
      return;
    }
    const assumptions = (report.assumptions || [])
      .slice(0, 4)
      .map((item) => `<li>${escapeHtml(item.heading || "문항")} · ${escapeHtml(item.requiredAction || "")}</li>`)
      .join("");
    root.innerHTML = `
      <article class="ops-card ${report.status === "locked" ? "ok" : "needs_work"}">
        <span>근거 잠금 게이트</span>
        <strong>${escapeHtml(report.exportGate || "")} · 보완 ${Number(report.needsGroundingSections || 0)}개 · 고위험 ${Number(report.highRiskClaims || 0)}개</strong>
        <p>${escapeHtml(report.message || "")}</p>
        <ul>${assumptions}</ul>
      </article>
    `;
  });
}

function renderConsultantReview() {
  const targets = [qs("#consultantReview"), qs("#exportConsultantReview")].filter(Boolean);
  const review = state.plan?.consultantReview;
  targets.forEach((root) => {
    if (!review) {
      root.innerHTML = "";
      return;
    }
    const fixes = (review.topFixes || [])
      .slice(0, 5)
      .map((item) => `<li>${Number(item.priority || 0)}. ${escapeHtml(item.area || "")} · ${escapeHtml(item.action || "")}</li>`)
      .join("");
    root.innerHTML = `
      <article class="ops-card ${escapeAttr(review.status || "")}">
        <span>컨설턴트 최종 리뷰</span>
        <strong>${Number(review.readinessScore || 0)}점 · ${escapeHtml(review.decision || "")}</strong>
        <ul>${fixes}</ul>
      </article>
    `;
  });
}

function renderJudgeReviewPack() {
  const targets = [qs("#judgeReviewPack"), qs("#exportJudgeReviewPack")].filter(Boolean);
  const pack = state.plan?.judgeReviewPack;
  targets.forEach((root) => {
    if (!pack) {
      root.innerHTML = "";
      return;
    }
    const questions = (pack.judgeQuestions || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    const risks = (pack.rejectionRisks || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    root.innerHTML = `
      <article class="ops-card ${escapeAttr(pack.status || "")}">
        <span>심사위원 예상 질문</span>
        <strong>${Number((pack.judgeQuestions || []).length)}개 질문 · ${Number((pack.rejectionRisks || []).length)}개 리스크</strong>
        <div class="ops-columns">
          <section><h4>질문</h4><ul>${questions || "<li>예상 질문이 없습니다.</li>"}</ul></section>
          <section><h4>리스크</h4><ul>${risks || "<li>주요 리스크가 없습니다.</li>"}</ul></section>
        </div>
      </article>
    `;
  });
}

function renderSecurityReport() {
  const targets = [qs("#securityReport"), qs("#exportSecurityReport")].filter(Boolean);
  const report = state.plan?.securityReport || state.documentInsights?.securityReport;
  targets.forEach((root) => {
    if (!report) {
      root.innerHTML = "";
      return;
    }
    const actions = (report.recommendedActions || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    root.innerHTML = `
      <article class="ops-card ${escapeAttr(report.status || "")}">
        <span>보안·개인정보 점검</span>
        <strong>민감문서 ${Number(report.restrictedDocumentCount || 0)}건 · Git 보호 ${report.gitignoreProtected ? "정상" : "확인 필요"}</strong>
        <ul>${actions}</ul>
      </article>
    `;
  });
}

function renderAiCostLedger() {
  const targets = [qs("#aiCostLedger"), qs("#exportAiCostLedger")].filter(Boolean);
  const ledger = state.plan?.aiCostLedger;
  targets.forEach((root) => {
    if (!ledger) {
      root.innerHTML = "";
      return;
    }
    const rows = (ledger.rows || [])
      .map((row) => `<li>${escapeHtml(row.stage || "")} · ${escapeHtml(row.model || "")} · $${Number(row.estimatedUsd || 0).toFixed(4)}</li>`)
      .join("");
    root.innerHTML = `
      <article class="ops-card estimated">
        <span>AI 비용 추정 원장</span>
        <strong>$${Number(ledger.estimatedTotalUsd || 0).toFixed(4)} ${escapeHtml(ledger.currency || "USD")}</strong>
        <ul>${rows}</ul>
      </article>
    `;
  });
}

function renderSecureTransferPolicy() {
  const targets = [qs("#secureTransferPolicy"), qs("#exportSecureTransferPolicy")].filter(Boolean);
  const policy = state.plan?.secureTransferPolicy;
  targets.forEach((root) => {
    if (!policy) {
      root.innerHTML = "";
      return;
    }
    const rows = (policy.policy || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    root.innerHTML = `
      <article class="ops-card ${policy.status === "ok" ? "ok" : "needs_review"}">
        <span>민감문서 전송 정책</span>
        <strong>민감문서 ${Number(policy.restrictedDocumentCount || 0)}건 · 외부 API ${policy.externalApiConfigured ? "설정됨" : "미설정"}</strong>
        <p>AI 전송 전 확인 필요: ${policy.requiresUserConfirmationBeforeAiTransfer ? "예" : "아니오"}</p>
        <ul>${rows}</ul>
      </article>
    `;
  });
}

function renderWorkspaceManagement() {
  const targets = [qs("#workspaceManagement"), qs("#exportWorkspaceManagement")].filter(Boolean);
  const workspace = state.plan?.workspaceManagement;
  targets.forEach((root) => {
    if (!workspace) {
      root.innerHTML = "";
      return;
    }
    const actions = (workspace.recommendedActions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    root.innerHTML = `
      <article class="ops-card ok">
        <span>프로젝트 관리</span>
        <strong>${escapeHtml(workspace.profileId || "default-workspace")} · 문서 ${Number(workspace.documentCount || 0)}개 · 버전 ${Number(workspace.versionCount || 0)}개</strong>
        <ul>${actions}</ul>
      </article>
    `;
  });
}

function renderEvidenceTraceability() {
  const targets = [qs("#evidenceTraceability"), qs("#exportEvidenceTraceability")].filter(Boolean);
  const trace = state.plan?.evidenceTraceability;
  targets.forEach((root) => {
    if (!trace) {
      root.innerHTML = "";
      return;
    }
    const sections = (trace.sections || [])
      .map((section) => {
        const evidence = (section.matchedEvidence || [])
          .slice(0, 3)
          .map(
            (item) => `
              <li>
                <span>${escapeHtml(item.areaLabel || "원문 근거")} · ${escapeHtml(item.source || "")} · ${Number(item.matchScore || 0)}점</span>
                <p>${escapeHtml(item.text || "")}</p>
              </li>
            `
          )
          .join("");
        const suggested = !evidence
          ? (section.suggestedEvidence || [])
              .slice(0, 2)
              .map((item) => `<li><span>${escapeHtml(item.areaLabel || "보강 근거")} · ${escapeHtml(item.source || "")}</span><p>${escapeHtml(item.text || "")}</p></li>`)
              .join("")
          : "";
        return `
          <article class="trace-section ${escapeAttr(section.status || "")}">
            <div>
              <span>${escapeHtml(traceStatusLabel(section.status))}</span>
              <strong>${escapeHtml(section.heading || "문항")}</strong>
              <small>근거점수 ${Number(section.supportScore || 0)}점 · 후보 ${Number(section.availableEvidence || 0)}개</small>
            </div>
            ${(evidence || suggested) ? `<ol>${evidence || suggested}</ol>` : `<p class="hint">연결 가능한 원문 근거가 부족합니다.</p>`}
          </article>
        `;
      })
      .join("");
    root.innerHTML = `
      <article class="trace-hero ${escapeAttr(trace.status || "")}">
        <span>원문 근거 추적성</span>
        <strong>${Number(trace.groundedSections || 0)}개 충분 · ${Number(trace.partialSections || 0)}개 부분 · ${Number(trace.needsGroundingSections || 0)}개 보강 필요</strong>
        <p>평균 근거점수 ${Number(trace.averageSupportScore || 0)}점. 각 문항이 업로드 문서의 어떤 원문 근거를 사용했는지 확인합니다.</p>
      </article>
      ${sections}
    `;
  });
}

function renderUnsupportedClaimAudit() {
  const targets = [qs("#unsupportedClaimAudit"), qs("#exportUnsupportedClaimAudit")].filter(Boolean);
  const audit = state.plan?.unsupportedClaimAudit;
  targets.forEach((root) => {
    if (!audit) {
      root.innerHTML = "";
      return;
    }
    const claims = (audit.claims || [])
      .map(
        (claim) => `
          <article class="claim-item ${escapeAttr(claim.severity || "")}">
            <span>${escapeHtml(claim.severity === "high" ? "고위험" : "주의")}</span>
            <strong>${escapeHtml(claim.heading || "문항")}</strong>
            <p>${escapeHtml(claim.claim || "")}</p>
            <small>${escapeHtml(claim.reason || "")}</small>
          </article>
        `
      )
      .join("");
    root.innerHTML = `
      <article class="claim-hero ${escapeAttr(audit.status || "")}">
        <span>근거 없는 주장 점검</span>
        <strong>고위험 ${Number(audit.highRiskClaims || 0)}건 · 주의 ${Number(audit.mediumRiskClaims || 0)}건</strong>
        <p>업로드 원문에 없는 숫자, 성과, 과장 표현이 초안에 새로 생겼는지 확인합니다.</p>
      </article>
      ${claims || `<article class="claim-item ok"><strong>검출된 위험 주장이 없습니다.</strong><p>현재 초안의 주요 숫자와 강한 표현은 업로드 근거 범위 안에서 관리되고 있습니다.</p></article>`}
    `;
  });
}

function traceStatusLabel(status) {
  const labels = {
    grounded: "근거 충분",
    partial: "부분 연결",
    needs_grounding: "보강 필요",
    no_source: "근거 없음",
  };
  return labels[status] || "확인";
}

async function exportPlan() {
  if (!state.plan) {
    setStatus("먼저 초안을 생성하세요.");
    activatePanel("draft");
    return;
  }
  setStatus("파일 생성 중");
  const result = await api("/api/export/hwpx", {
    method: "POST",
    body: JSON.stringify({ plan: state.plan }),
  });
  renderExports(result);
  activatePanel("export");
  setStatus(result.blocked ? "근거 보완 필요: export가 차단되었습니다." : "파일 생성 완료");
}

function renderExports(result) {
  const root = qs("#exportResults");
  if (!result) {
    root.className = "export-list empty-state";
    root.textContent = "생성된 파일이 없습니다.";
    return;
  }
  if (result.blocked) {
    root.className = "export-list blocked";
    root.innerHTML = `
      <article class="export-item export-blocked">
        <div>
          <strong>제출 전 보완이 필요합니다</strong>
          <p class="micro">${escapeHtml(result.error || "근거 또는 보안 검증을 통과하지 못했습니다.")}</p>
          <ul class="compact-list">
            ${(result.blockers || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </div>
      </article>
    `;
    return;
  }
  root.className = "export-list";
  root.innerHTML = (result.files || [])
    .map(
      (file) => `
        <article class="export-item">
          <div>
            <strong>${escapeHtml(exportLabel(file))}</strong>
            <p class="micro">${escapeHtml(file.filename)}</p>
          </div>
          <button class="download-btn" type="button" data-download-url="${escapeAttr(file.url)}">다운로드</button>
        </article>
      `
    )
    .join("");
  bindDownloadButtons(root);
}

function exportLabel(file) {
  const name = String(file.filename || "");
  if (name.endsWith(".hwpx")) return "HWPX 사업계획서";
  if (name.endsWith(".html")) return "검토용 HTML";
  if (name.endsWith(".json") && name.includes("template-answer-map")) return "양식-답변 매핑 JSON";
  if (name.endsWith(".json")) return "초안 데이터 JSON";
  if (name.endsWith(".zip")) return "원본 양식 보존 패키지 ZIP";
  if (name.includes("original-template")) return "원본 제출양식";
  return file.label || "생성 파일";
}

async function autoSaveDraftVersion(label, source = "auto") {
  if (!state.plan) return null;
  syncDraftTextareas();
  const profileId = state.activeProfileId || "default-workspace";
  const result = await api("/api/versions", {
    method: "POST",
    body: JSON.stringify({
      profileId,
      label,
      source,
      plan: state.plan,
      workspace: currentWorkspacePayload(),
    }),
  });
  state.versions = result.versions || [];
  state.currentVersionId = result.version?.id || state.currentVersionId;
  renderVersionSelect();
  return result.version;
}

async function loadVersions() {
  const profileId = state.activeProfileId || "default-workspace";
  try {
    const result = await api(`/api/versions?profileId=${encodeURIComponent(profileId)}`);
    state.versions = result.versions || [];
  } catch {
    state.versions = [];
  }
  renderVersionSelect();
}

function renderVersionSelect() {
  const select = qs("#versionSelect");
  const baseSelect = qs("#revisionBaseSelect");
  if (!state.versions.length) {
    if (select) select.innerHTML = `<option value="">저장된 버전 없음</option>`;
    if (baseSelect) baseSelect.innerHTML = `<option value="">현재 화면의 초안 기준</option>`;
    renderVersionList();
    return;
  }
  const versionOptions = [
    `<option value="">버전 선택</option>`,
    ...state.versions.map((version) => {
      const label = `${version.label || "초안"} · ${version.createdAt || ""}`;
      return `<option value="${escapeAttr(version.id)}"${version.id === state.currentVersionId ? " selected" : ""}>${escapeHtml(label)}</option>`;
    }),
  ].join("");
  if (select) select.innerHTML = versionOptions;
  if (baseSelect) {
    baseSelect.innerHTML = [
      `<option value="">현재 화면의 초안 기준</option>`,
      ...state.versions.map((version) => {
        const label = `${version.label || "초안"} · ${version.createdAt || ""}`;
        return `<option value="${escapeAttr(version.id)}"${version.id === state.currentVersionId ? " selected" : ""}>${escapeHtml(label)}</option>`;
      }),
    ].join("");
  }
  renderVersionList();
}

function renderVersionList() {
  const root = qs("#versionList");
  if (!root) return;
  if (!state.versions.length) {
    root.className = "version-list empty-state";
    root.textContent = "저장된 초안 버전이 없습니다.";
    return;
  }
  root.className = "version-list";
  root.innerHTML = state.versions
    .map((version) => {
      const files = state.versionExports[version.id]?.files || [];
      const fileLinks = files.length
        ? `<div class="version-files">${files
            .map((file) => `<button type="button" data-download-url="${escapeAttr(file.url)}">${escapeHtml(exportLabel(file))}</button>`)
            .join("")}</div>`
        : "";
      return `
        <article class="version-card ${version.id === state.currentVersionId ? "active" : ""}">
          <div>
            <span class="tag">${escapeHtml(version.source || "manual")}</span>
            <strong>${escapeHtml(version.label || "초안")}</strong>
            <p class="micro">${escapeHtml(version.createdAt || "")}${version.updatedAt ? ` · 수정 ${escapeHtml(version.updatedAt)}` : ""}</p>
            <p class="hint">${escapeHtml(version.companyName || "")} · ${escapeHtml(version.grantName || "")} · ${escapeHtml(version.sectionCount || 0)}개 섹션 · ${escapeHtml(version.score || "-")}점</p>
          </div>
          <div class="version-actions">
            <button class="ghost-btn" type="button" data-version-open="${escapeAttr(version.id)}">열기·수정</button>
            <button class="ghost-btn" type="button" data-version-export="${escapeAttr(version.id)}">다운로드 생성</button>
          </div>
          ${fileLinks}
        </article>
      `;
    })
    .join("");
  root.querySelectorAll("[data-version-open]").forEach((button) => {
    button.addEventListener("click", () => restoreDraftVersion(button.dataset.versionOpen));
  });
  root.querySelectorAll("[data-version-export]").forEach((button) => {
    button.addEventListener("click", () => exportDraftVersion(button.dataset.versionExport));
  });
  bindDownloadButtons(root);
}

async function saveDraftVersion() {
  if (!state.plan) {
    setStatus("저장할 초안이 없습니다.");
    activatePanel("draft");
    return;
  }
  syncDraftTextareas();
  const label = qs("#versionLabel").value.trim() || `${state.plan.grantName || "지원사업"} 검토본`;
  const profileId = state.activeProfileId || "default-workspace";
  setStatus("초안 버전 저장 중");
  const result = await api("/api/versions", {
    method: "POST",
    body: JSON.stringify({
      profileId,
      label,
      source: "manual",
      plan: state.plan,
      workspace: currentWorkspacePayload(),
    }),
  });
  state.versions = result.versions || [];
  state.currentVersionId = result.version?.id || state.currentVersionId;
  qs("#versionLabel").value = "";
  renderVersionSelect();
  setStatus("초안 버전 저장 완료");
}

async function restoreDraftVersion(versionIdArg = "") {
  const versionId = versionIdArg || qs("#versionSelect").value;
  if (!versionId) {
    setStatus("불러올 버전을 선택하세요.");
    return;
  }
  const profileId = state.activeProfileId || "default-workspace";
  setStatus("초안 버전 불러오는 중");
  const result = await api(`/api/versions/${encodeURIComponent(profileId)}/${encodeURIComponent(versionId)}`);
  const version = result.version;
  state.currentVersionId = version.id || versionId;
  state.plan = version.plan || null;
  if (version.workspace) {
    state.template = version.workspace.template || state.template;
    state.documentInsights = version.workspace.documentInsights || state.documentInsights;
    state.templateGuidance = version.workspace.templateGuidance || state.templateGuidance;
    restoreWorkspaceInputs(version.workspace);
  }
  renderAnalysis();
  renderDocumentInsights();
  renderDraft();
  renderVersionSelect();
  activatePanel("draft");
  setStatus("초안 버전 불러오기 완료");
}

async function reviseDraftFromComments() {
  const comments = qs("#revisionComments").value.trim();
  if (!comments) {
    setStatus("반영할 코멘트를 입력하세요.");
    return;
  }
  if (!state.plan && !qs("#revisionBaseSelect").value) {
    setStatus("먼저 기준 사업계획서를 생성하거나 버전을 선택하세요.");
    return;
  }
  syncDraftTextareas();
  const profileId = state.activeProfileId || "default-workspace";
  const baseVersionId = qs("#revisionBaseSelect").value || "";
  const label = qs("#versionLabel").value.trim() || `코멘트 반영본 ${new Date().toLocaleString("ko-KR")}`;
  setStatus("코멘트 반영 새 버전 생성 중");
  const result = await api("/api/versions/revise", {
    method: "POST",
    body: JSON.stringify({
      profileId,
      versionId: baseVersionId,
      label,
      comments,
      plan: state.plan,
      workspace: currentWorkspacePayload(),
    }),
  });
  state.plan = result.plan;
  state.versions = result.versions || [];
  state.currentVersionId = result.version?.id || state.currentVersionId;
  qs("#revisionComments").value = "";
  qs("#versionLabel").value = "";
  renderDraft();
  renderVersionSelect();
  setStatus("코멘트 반영 새 버전 생성 완료");
}

async function updateCurrentVersion() {
  const versionId = state.currentVersionId || qs("#versionSelect").value;
  if (!versionId) {
    setStatus("업데이트할 버전을 먼저 열거나 선택하세요.");
    return;
  }
  if (!state.plan) {
    setStatus("저장할 초안이 없습니다.");
    return;
  }
  syncDraftTextareas();
  const label = qs("#versionLabel").value.trim() || state.versions.find((item) => item.id === versionId)?.label || "수정본";
  const profileId = state.activeProfileId || "default-workspace";
  setStatus("선택 버전 업데이트 중");
  const result = await api("/api/versions/update", {
    method: "POST",
    body: JSON.stringify({
      profileId,
      versionId,
      label,
      source: "edited",
      plan: state.plan,
      workspace: currentWorkspacePayload(),
    }),
  });
  state.versions = result.versions || [];
  state.currentVersionId = result.version?.id || versionId;
  qs("#versionLabel").value = "";
  renderVersionSelect();
  setStatus("선택 버전 업데이트 완료");
}

async function exportDraftVersion(versionIdArg = "") {
  const versionId = versionIdArg || qs("#versionSelect").value || state.currentVersionId;
  if (!versionId) {
    setStatus("다운로드할 버전을 선택하세요.");
    return;
  }
  const profileId = state.activeProfileId || "default-workspace";
  setStatus("선택 버전 다운로드 파일 생성 중");
  const result = await api(`/api/versions/${encodeURIComponent(profileId)}/${encodeURIComponent(versionId)}/export`);
  state.versionExports[versionId] = result;
  renderVersionList();
  renderVersionExportResults(result);
  setStatus(result.blocked ? "근거 보완 필요: 선택 버전 export가 차단되었습니다." : "선택 버전 다운로드 파일 생성 완료");
}

function renderVersionExportResults(result) {
  const root = qs("#versionExportResults");
  if (!root || !result) return;
  if (result.blocked) {
    root.innerHTML = `
      <article class="export-item export-blocked">
        <div>
          <strong>선택 버전 제출 전 보완이 필요합니다</strong>
          <p class="micro">${escapeHtml(result.error || "근거 또는 보안 검증을 통과하지 못했습니다.")}</p>
          <ul class="compact-list">
            ${(result.blockers || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </div>
      </article>
    `;
    return;
  }
  root.innerHTML = (result.files || [])
    .map(
      (file) => `
        <article class="export-item">
          <div>
            <strong>${escapeHtml(exportLabel(file))}</strong>
            <p class="micro">${escapeHtml(result.version?.label || "")} · ${escapeHtml(file.filename)}</p>
          </div>
          <button class="download-btn" type="button" data-download-url="${escapeAttr(file.url)}">다운로드</button>
        </article>
      `
    )
    .join("");
  bindDownloadButtons(root);
}

function syncDraftTextareas() {
  if (!state.plan?.sections) return;
  document.querySelectorAll("[data-draft]").forEach((textarea) => {
    const section = state.plan.sections.find((item) => String(item.id) === textarea.dataset.draft);
    if (section) section.content = textarea.value;
  });
}

function renderMetrics() {
  const company = collectCompanySafe();
  qs("#currentCompany").textContent = company.basic?.name || "미입력";
  qs("#docCountMetric").textContent = state.documentInsights?.documents?.length || 0;
  qs("#questionMetric").textContent = state.template?.questions?.length || 0;
  qs("#sectionMetric").textContent = state.plan?.sections?.length || 0;
}

function activatePanel(id) {
  document.querySelectorAll(".panel").forEach((panel) => panel.classList.toggle("active", panel.id === id));
  document.querySelectorAll(".step").forEach((step) => step.classList.toggle("active", step.dataset.target === id));
}

function categoryLabel(category) {
  const labels = {
    overview: "개요",
    problem: "문제",
    solution: "솔루션",
    market: "시장",
    differentiation: "차별성",
    business_model: "수익",
    growth: "성장",
    budget: "예산",
    team: "팀",
    impact: "효과",
    risk: "리스크",
  };
  return labels[category] || "문항";
}

function countPatch(patch) {
  let count = 0;
  Object.values(patch || {}).forEach((value) => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      count += countPatch(value);
    } else if (String(value || "").trim()) {
      count += 1;
    }
  });
  return count;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll('"', "&quot;");
}

async function boot() {
  document.querySelectorAll(".step").forEach((button) => {
    button.addEventListener("click", () => activatePanel(button.dataset.target));
  });
  qs("#saveCompanyBtn").addEventListener("click", saveCompany);
  qs("#profileSelect").addEventListener("change", (event) => {
    loadProfile(event.target.value);
  });
  qs("#analyzeDocsBtn").addEventListener("click", analyzeDocuments);
  qs("#applyDocPatchBtn").addEventListener("click", applyDocumentPatch);
  qs("#analyzeBtn").addEventListener("click", analyzeTemplate);
  qs("#generateBtn").addEventListener("click", generateDraft);
  qs("#exportBtn").addEventListener("click", exportPlan);
  qs("#saveVersionBtn").addEventListener("click", saveDraftVersion);
  qs("#restoreVersionBtn").addEventListener("click", restoreDraftVersion);
  qs("#reviseBtn").addEventListener("click", reviseDraftFromComments);
  qs("#updateVersionBtn").addEventListener("click", updateCurrentVersion);
  qs("#versionSelect").addEventListener("change", (event) => {
    state.currentVersionId = event.target.value || state.currentVersionId;
    renderVersionList();
  });

  try {
    await Promise.allSettled([loadAiSettings(), loadGrantDataset()]);
    await loadProfiles();
    if (state.activeProfileId) {
      await loadProfile(state.activeProfileId);
    } else {
      state.company = normalizeCompany({});
      renderCompanyForm();
      renderDocumentInsights();
      renderAnalysis();
      renderDraft();
      await loadVersions();
      setStatus("새 회사 프로필 작성 중");
    }
  } catch (error) {
    state.company = normalizeCompany({});
    renderCompanyForm();
    renderProfileSelect();
    renderAiEngine();
    setStatus(error.message);
  }
}

boot();

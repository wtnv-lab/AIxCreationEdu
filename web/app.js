const manifestPath = "config/web_content.json";
const homeHash = "home";
const githubUrl = "https://github.com/wtnv-lab/AIxCreationEdu";

const state = {
  items: [],
  project: {},
  activeSection: "home",
  activeMenuSection: "reports",
  activePath: "",
  markdownCache: new Map(),
  contentByPath: new Map(),
};

const els = {
  list: document.querySelector("#content-list"),
  kicker: document.querySelector("#document-kicker"),
  title: document.querySelector("#document-title"),
  meta: document.querySelector("#document-meta"),
  body: document.querySelector("#document-body"),
};

init();

async function init() {
  bindEvents();
  setDocumentLoading(null, "トップページを読み込んでいます");

  try {
    const manifest = await fetchJson(manifestPath);
    state.project = manifest.project || {};
    state.items = manifest.content || [];
    state.contentByPath = new Map(state.items.map((item) => [item.path, item]));

    const initialPath = getPathFromHash();

    if (!initialPath || initialPath === homeHash) {
      showHome({ updateHash: false });
    } else if (state.contentByPath.has(initialPath)) {
      const item = state.contentByPath.get(initialPath);
      setActiveSection(item.section);
      await selectItem(initialPath, { updateHash: false });
    } else {
      showHome({ updateHash: true });
    }

    preloadText();
  } catch (error) {
    renderFatalError(error);
  }
}

function bindEvents() {
  els.body.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-path]");
    if (!button) return;

    const text = state.markdownCache.get(button.dataset.copyPath);
    if (!text) return;

    await copyText(stripFirstHeading(text).trim(), button);
  });

  window.addEventListener("hashchange", async () => {
    const path = getPathFromHash();
    if (!path || path === homeHash) {
      showHome({ updateHash: false });
      return;
    }

    if (path && path !== state.activePath && state.contentByPath.has(path)) {
      setActiveSection(state.contentByPath.get(path).section);
      await selectItem(path, { updateHash: false });
    }
  });
}

async function copyText(text, button) {
  const original = button.textContent;

  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "コピー済み";
  } catch {
    button.textContent = "選択してコピー";
  }

  window.setTimeout(() => {
    button.textContent = original;
  }, 1800);
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`${path} を読み込めませんでした`);
  }
  return response.json();
}

async function fetchText(path) {
  if (state.markdownCache.has(path)) {
    return state.markdownCache.get(path);
  }

  const response = await fetch(path, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`${path} を読み込めませんでした`);
  }

  const text = await response.text();
  state.markdownCache.set(path, text);
  return text;
}

function getPathFromHash() {
  const raw = window.location.hash.slice(1);
  if (!raw) return "";

  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

function setHash(path) {
  const encoded = path === homeHash ? homeHash : encodeURIComponent(path);
  if (window.location.hash.slice(1) !== encoded) {
    window.location.hash = encoded;
  }
}

function setActiveSection(section) {
  state.activeSection = section;
  document.body.dataset.section = section || "home";
}

function setActiveMenuSection(section) {
  if (section === "reports" || section === "prompts") {
    state.activeMenuSection = section;
  }
}

function renderNavigation() {
  els.list.textContent = "";

  const fragment = document.createDocumentFragment();
  const section = getActiveMenuSection();
  fragment.append(createCategorySelector());
  fragment.append(createSectionList(getSectionTitle(section), getItemsBySection(section), section));

  els.list.append(fragment);
}

function renderGithubIcon(className = "") {
  const classes = `github-icon ${className}`.trim();
  return `<span class="${escapeAttr(classes)}" aria-hidden="true">${githubIconSvg()}</span>`;
}

function githubIconSvg() {
  return `<svg viewBox="0 0 24 24" focusable="false"><path d="M12 0.3C5.37 0.3 0 5.67 0 12.3c0 5.31 3.44 9.8 8.21 11.39 0.6 0.11 0.82-0.26 0.82-0.58 0-0.29-0.01-1.24-0.02-2.25-3.34 0.73-4.04-1.42-4.04-1.42-0.55-1.39-1.34-1.76-1.34-1.76-1.09-0.75 0.08-0.73 0.08-0.73 1.21 0.09 1.85 1.24 1.85 1.24 1.07 1.84 2.82 1.31 3.51 1 0.11-0.78 0.42-1.31 0.76-1.61-2.67-0.3-5.47-1.33-5.47-5.93 0-1.31 0.47-2.38 1.24-3.22-0.12-0.3-0.54-1.52 0.12-3.18 0 0 1.01-0.32 3.3 1.23 0.96-0.27 1.98-0.4 3-0.4s2.04 0.13 3 0.4c2.29-1.55 3.3-1.23 3.3-1.23 0.66 1.66 0.24 2.88 0.12 3.18 0.77 0.84 1.23 1.91 1.23 3.22 0 4.61-2.81 5.62-5.48 5.92 0.43 0.37 0.81 1.1 0.81 2.22 0 1.61-0.01 2.9-0.01 3.29 0 0.32 0.22 0.7 0.83 0.58A12.02 12.02 0 0 0 24 12.3C24 5.67 18.63 0.3 12 0.3Z"></path></svg>`;
}

function createCategorySelector() {
  const nav = document.createElement("nav");
  nav.className = "side-category-selector";
  nav.setAttribute("aria-label", "カテゴリ選択");

  [
    { label: "レポート", section: "reports" },
    { label: "プロンプト", section: "prompts" },
  ].forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "side-category-button";
    button.dataset.section = category.section;
    button.classList.toggle("is-active", getActiveMenuSection() === category.section);
    button.setAttribute("aria-pressed", getActiveMenuSection() === category.section ? "true" : "false");
    button.addEventListener("click", () => selectFirstItem(category.section));

    const label = document.createElement("span");
    label.className = "side-category-name";
    label.textContent = category.label;

    const count = document.createElement("span");
    count.className = "side-category-count";
    count.textContent = `${getItemsBySection(category.section).length}件`;

    button.append(label, count);
    nav.append(button);
  });

  return nav;
}

function getActiveMenuSection() {
  return state.activeMenuSection === "prompts" ? "prompts" : "reports";
}

function getSectionTitle(section) {
  return section === "prompts" ? "プロンプト" : "レポート";
}

function selectFirstItem(section) {
  setActiveMenuSection(section);
  const item = getItemsBySection(section)[0];
  if (item) {
    selectItem(item.path);
  } else {
    renderNavigation();
  }
}

function createSectionList(title, items, sectionName) {
  const section = document.createElement("section");
  section.className = "nav-section";
  section.classList.toggle("is-current", state.activeSection === sectionName);

  const heading = document.createElement("h2");
  heading.className = "nav-section-title";
  heading.textContent = title;
  section.append(heading);

  if (items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "nav-empty";
    empty.textContent = "表示できる項目がありません。";
    section.append(empty);
    return section;
  }

  const fragment = document.createDocumentFragment();
  items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "content-item";
    button.classList.toggle("is-active", item.path === state.activePath);
    button.addEventListener("click", () => selectItem(item.path));

    const title = document.createElement("span");
    title.className = "item-title";
    title.textContent = item.title;
    title.title = item.title;

    const summary = document.createElement("p");
    summary.className = "item-summary";
    summary.textContent = item.summary || item.path;

    button.append(title, summary);

    fragment.append(button);
  });

  section.append(fragment);
  return section;
}

function getItemsBySection(section) {
  return state.items.filter((item) => item.section === section);
}

async function selectItem(path, options = {}) {
  const item = state.contentByPath.get(path);
  if (!item) return;

  state.activePath = path;
  setActiveSection(item.section);
  setActiveMenuSection(item.section);
  renderNavigation();
  setDocumentLoading(item);
  resetScrollPosition();

  if (options.updateHash !== false) {
    setHash(path);
  }

  try {
    const text = await fetchText(item.path);
    renderDocument(item, text);
    resetScrollPosition();
  } catch (error) {
    renderDocumentError(item, error);
    resetScrollPosition();
  }
}

function setDocumentLoading(item = null, message = "本文を読み込んでいます") {
  els.kicker.textContent = item ? getKindLabel(item) : "読み込み中";
  els.title.textContent = item ? item.title : "文書を読み込んでいます";
  els.meta.textContent = "";
  els.body.innerHTML = `<div class="loading">${escapeHtml(message)}。</div>`;
}

function renderDocument(item, text) {
  els.kicker.textContent = getKindLabel(item);
  els.title.textContent = item.title;
  renderMeta(item);
  els.body.classList.remove("code-body");
  els.body.innerHTML =
    item.section === "prompts"
      ? renderPromptSnippet(text, item)
      : renderReportMarkdown(text, item.path);
}

function renderMeta(item) {
  els.meta.textContent = "";
  (item.authors || []).forEach((value) => {
    const pill = document.createElement("span");
    pill.className = "meta-pill";
    pill.textContent = value;
    els.meta.append(pill);
  });

  const source = document.createElement("a");
  source.className = "meta-pill meta-link";
  source.href = getGithubFileUrl(item.path);
  source.target = "_blank";
  source.rel = "noopener";
  source.textContent = item.path;
  els.meta.append(source);
}

function renderEmptyDocument() {
  els.kicker.textContent = "文書なし";
  els.title.textContent = "表示できる文書がありません";
  els.meta.textContent = "";
  els.body.classList.remove("code-body");
  els.body.innerHTML = `<div class="empty-state">表示できるファイルの一覧が空です。</div>`;
}

function renderDocumentError(item, error) {
  els.kicker.textContent = getKindLabel(item);
  els.title.textContent = item.title;
  els.meta.textContent = "";
  els.body.classList.remove("code-body");
  els.body.innerHTML = `<div class="error-state">${escapeHtml(error.message)}。ローカルではHTTPサーバ経由で開いてください。</div>`;
}

function renderFatalError(error) {
  els.list.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
  els.kicker.textContent = "読み込み失敗";
  els.title.textContent = "文書一覧を読み込めません";
  els.meta.textContent = "";
  els.body.classList.remove("code-body");
  els.body.innerHTML = `<div class="error-state">${escapeHtml(error.message)}。ローカルではHTTPサーバ経由で開いてください。</div>`;
}

function getGithubFileUrl(path) {
  return `${githubUrl}/blob/main/${path.split("/").map(encodeURIComponent).join("/")}`;
}

function getKindLabel(item) {
  if (item.section === "prompts") return "プロンプト";
  return "レポート";
}

function preloadText() {
  state.items.forEach((item) => {
    fetchText(item.path).catch(() => {});
  });
}

function showHome(options = {}) {
  state.activePath = "";
  setActiveSection("home");
  setActiveMenuSection("reports");
  renderNavigation();
  if (options.updateHash !== false) setHash(homeHash);
  els.kicker.textContent = "トップ";
  els.title.textContent = state.project.title || "AIとクリエイティブと教育";
  els.meta.textContent = "";
  els.body.classList.remove("code-body");
  els.body.innerHTML = renderHome();
  resetScrollPosition();
}

function resetScrollPosition() {
  window.requestAnimationFrame(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  });
}

function renderHome() {
  const description =
    state.project.description ||
    "生成AI時代の創造性、表現、情報リテラシー、教育実践を横断的に検討する公開レポート集。";
  const homeSubtitle = description.replace(/。$/, "");
  const reportCount = state.items.filter((item) => item.section === "reports").length;
  const promptCount = state.items.filter((item) => item.section === "prompts").length;

  return `
    <section class="home-intro">
      <blockquote class="lead"><p>${escapeHtml(homeSubtitle)}</p></blockquote>
      <p class="purpose-text">本サイトは、東京大学大学院 渡邉英徳研究室と関係者が蓄積してきた、AI・クリエイティブ・教育に関する実践・研究データをもとにした公開レポート集です。研究資料、実践記録、参考文献を生成AIが処理し、著者との対話を通じて構成した内容を、人間が確認・編集し、読みやすい形で公開しています。AIが構造と内容を理解しやすいMarkdown本文・メタデータ・プロンプト一式は、GitHubで公開しています。</p>
    </section>
    <figure class="home-figure">
      <img src="assets/00-overview/project-concept-map.svg" alt="AIとクリエイティブと教育の概念図">
      <figcaption>AIとクリエイティブと教育の概念図</figcaption>
    </figure>
    <section class="corner-grid" aria-label="資料の入口">
      ${renderCornerCard("レポート", `${reportCount}件`, "著者の研究リソースをもとに、生成AIとの対話で編んだ本文を読みやすく整理しています。", "reports")}
      ${renderCornerCard("プロンプト", `${promptCount}件`, "リポジトリ全体や単一テキストをAIに渡したあと、授業案や企画づくりに使えます。", "prompts")}
      ${renderExternalCornerCard("ソースコード", "AIが構造と内容を理解しやすいMarkdown、メタデータ、プロンプト一式をGitHubで公開しています。", githubUrl)}
    </section>
    <section>
      <h2>まず読むなら</h2>
      <p>全体像をつかむ場合は「AIとクリエイティブと教育 総括レポート」から読み始めると、各レポートの位置づけが分かりやすくなります。授業や研修を作りたい場合は、レポートを読んだあと、AIに資料一式を読み込ませてからプロンプトを使ってください。</p>
    </section>
    ${renderProjectAuthors()}
  `;
}

function renderProjectAuthors() {
  const authorGroups = state.project.authors || [];
  if (authorGroups.length === 0) return "";

  return `
    <section class="authors-section">
      <h2>著者</h2>
      ${authorGroups.map(renderAuthorGroup).join("")}
    </section>
  `;
}

function renderAuthorGroup(group) {
  const members = group.members || [];
  return `
    <section class="author-group">
      <h3>${escapeHtml(group.affiliation || "所属未設定")}</h3>
      <ul>
        ${members.map((member) => `<li>${renderInline(member, "README.md")}</li>`).join("")}
      </ul>
    </section>
  `;
}

function renderCornerCard(title, count, summary, section) {
  const firstItem = state.items.find((item) => item.section === section);
  const href = firstItem ? `#${encodeURIComponent(firstItem.path)}` : "#home";
  return `
    <a class="corner-card" href="${href}">
      <span class="corner-count">${escapeHtml(count)}</span>
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(summary)}</p>
    </a>
  `;
}

function renderExternalCornerCard(title, summary, href) {
  return `
    <a class="corner-card" href="${escapeAttr(href)}" target="_blank" rel="noopener">
      <span class="corner-count">${renderGithubIcon("corner-github-icon")}</span>
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(summary)}</p>
    </a>
  `;
}

function renderPromptSnippet(text, item) {
  const snippet = stripFirstHeading(text).trim();
  return `
    ${renderPromptPurpose(item)}
    <section class="prompt-flow">
      <h2>使う前に</h2>
      <p>このプロンプトは、AIがこの資料集の内容を参照できる状態で使うためのものです。先にリポジトリ全体、または単一テキストファイルをAIに提供してください。</p>
      <div class="prompt-source-actions">
        <a href="ai/notebooklm-source.txt" target="_blank" rel="noopener">単一テキストを開く</a>
        <a href="${escapeAttr(githubUrl)}" target="_blank" rel="noopener">GitHubリポジトリを開く</a>
      </div>
    </section>
    <section class="snippet-panel">
      <div class="snippet-toolbar">
        <p>資料を読み込ませたあと、このスニペットをAIに貼り付けて使います。</p>
        <button class="copy-button" type="button" data-copy-path="${escapeAttr(item.path)}">コピー</button>
      </div>
      <pre class="prompt-snippet"><code>${escapeHtml(snippet)}</code></pre>
    </section>
  `;
}

function renderPromptPurpose(item) {
  const purpose = item.purpose || item.summary;
  if (!purpose) return "";

  return `
    <section class="prompt-purpose">
      <h2>主旨</h2>
      <p>${escapeHtml(purpose)}</p>
    </section>
  `;
}

function stripFirstHeading(markdown) {
  return markdown.replace(/^\s*#\s+.+(?:\r?\n)+/, "");
}

function renderReportMarkdown(markdown, sourcePath) {
  const body = stripFirstHeading(markdown);
  return renderMarkdownWithMetadata(body, sourcePath, extractReferenceUrls(body));
}

function renderMarkdownWithMetadata(markdown, sourcePath, referenceUrls = new Map()) {
  const metadataHeading = markdown.match(/^##\s+メタデータ\s*$/m);
  if (!metadataHeading) {
    return renderMarkdown(markdown, sourcePath, { referenceUrls });
  }

  const before = markdown.slice(0, metadataHeading.index);
  const metadataStart = metadataHeading.index + metadataHeading[0].length;
  const afterHeading = markdown.slice(metadataStart).replace(/^\r?\n/, "");
  const nextHeadingIndex = afterHeading.search(/^##\s+/m);
  const metadata = nextHeadingIndex >= 0 ? afterHeading.slice(0, nextHeadingIndex) : afterHeading;
  const afterMetadata = nextHeadingIndex >= 0 ? afterHeading.slice(nextHeadingIndex) : "";

  return `
    ${renderMarkdown(before, sourcePath, { referenceUrls })}
    <details class="metadata-details">
      <summary>メタデータ</summary>
      <div class="metadata-details-body">
        ${renderMarkdown(metadata, sourcePath, { referenceUrls })}
      </div>
    </details>
    ${renderMarkdown(afterMetadata, sourcePath, { referenceUrls })}
  `;
}

function renderMarkdown(markdown, sourcePath, options = {}) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i += 1;
      continue;
    }

    const fence = line.match(/^```(.*)$/);
    if (fence) {
      const language = fence[1].trim();
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1;
      html += `<pre><code${language ? ` data-language="${escapeAttr(language)}"` : ""}>${escapeHtml(code.join("\n"))}</code></pre>`;
      continue;
    }

    if (isTableStart(lines, i)) {
      const tableLines = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        tableLines.push(lines[i]);
        i += 1;
      }
      html += renderTable(tableLines, sourcePath, options);
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = Math.min(heading[1].length, 6);
      html += `<h${level}>${renderInline(heading[2], sourcePath, options)}</h${level}>`;
      i += 1;
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quote = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        quote.push(lines[i].replace(/^>\s?/, ""));
        i += 1;
      }
      html += `<blockquote>${renderMarkdown(quote.join("\n"), sourcePath, options)}</blockquote>`;
      continue;
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ""));
        i += 1;
      }
      html += `<ul>${items.map((item) => `<li>${renderInline(item, sourcePath, options)}</li>`).join("")}</ul>`;
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i += 1;
      }
      html += `<ol>${items.map((item) => `<li>${renderInline(item, sourcePath, options)}</li>`).join("")}</ol>`;
      continue;
    }

    if (/^\*図.+\*$/.test(line.trim())) {
      html += `<p class="figure-caption">${renderInline(line.trim().replace(/^\*|\*$/g, ""), sourcePath, options)}</p>`;
      i += 1;
      continue;
    }

    const paragraph = [];
    while (i < lines.length && lines[i].trim() && !isBlockStart(lines, i)) {
      paragraph.push(lines[i].trim());
      i += 1;
    }
    html += `<p>${renderInline(paragraph.join(" "), sourcePath, options)}</p>`;
  }

  return html;
}

function isBlockStart(lines, index) {
  const line = lines[index];
  return (
    /^```/.test(line) ||
    /^(#{1,6})\s+/.test(line) ||
    /^>\s?/.test(line) ||
    /^\s*[-*+]\s+/.test(line) ||
    /^\s*\d+\.\s+/.test(line) ||
    isTableStart(lines, index)
  );
}

function isTableStart(lines, index) {
  const current = lines[index] || "";
  const next = lines[index + 1] || "";
  return current.includes("|") && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(next);
}

function renderTable(tableLines, sourcePath, options = {}) {
  const rows = tableLines
    .filter((_, index) => index !== 1)
    .map((line) => splitTableRow(line));

  if (rows.length === 0) return "";

  const head = rows[0];
  const bodyRows = rows.slice(1);
  const headHtml = head.map((cell) => `<th>${renderInline(cell, sourcePath, options)}</th>`).join("");
  const bodyHtml = bodyRows
    .map((row) => `<tr>${row.map((cell) => `<td>${renderInline(cell, sourcePath, options)}</td>`).join("")}</tr>`)
    .join("");

  return `<table><thead><tr>${headHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`;
}

function splitTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function extractReferenceUrls(markdown) {
  const urls = new Map();
  const referenceStart = markdown.search(/^##\s+参考文献・関連資料\s*$/m);
  if (referenceStart < 0) return urls;

  const references = markdown.slice(referenceStart);
  references.split("\n").forEach((line) => {
    const match = line.match(/^(\d+)\.\s+.*?(https?:\/\/\S+)/);
    if (!match) return;
    urls.set(match[1], match[2].replace(/[)、。.,;:!?]+$/, ""));
  });

  return urls;
}

function renderInline(text, sourcePath, options = {}) {
  const placeholders = [];
  const store = (html) => {
    const index = placeholders.push(html) - 1;
    return `\uE000${index}\uE001`;
  };

  let output = text.replace(/`([^`]+)`/g, (_, code) => store(`<code>${escapeHtml(code)}</code>`));

  output = output.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, href) => {
    const resolved = resolveUrl(href, sourcePath, "image");
    return store(`<img src="${escapeAttr(resolved.url)}" alt="${escapeAttr(alt)}">`);
  });

  output = output.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => {
    const resolved = resolveUrl(href, sourcePath, "link");
    const target = resolved.internal ? "" : ` target="_blank" rel="noopener"`;
    return store(`<a href="${escapeAttr(resolved.url)}"${target}>${escapeHtml(label)}</a>`);
  });

  output = escapeHtml(output).replace(/&lt;br\s*\/?&gt;/gi, "<br>");
  output = autolinkBareUrls(output);
  output = linkReferenceNumbers(output, options.referenceUrls || new Map());

  output = output
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");

  placeholders.forEach((html, index) => {
    output = output.replace(`\uE000${index}\uE001`, html);
  });

  return output;
}

function linkReferenceNumbers(html, referenceUrls) {
  if (referenceUrls.size === 0) return html;

  return html.replace(/\[([0-9,\s]+)\]/g, (_, value) => {
    const parts = value.split(/(,\s*)/);
    const linked = parts
      .map((part) => {
        const number = part.trim();
        if (!/^\d+$/.test(number) || !referenceUrls.has(number)) return part;
        const href = referenceUrls.get(number);
        return `<a href="${escapeAttr(href)}" target="_blank" rel="noopener">${number}</a>`;
      })
      .join("");
    return `[${linked}]`;
  });
}

function autolinkBareUrls(html) {
  return html.replace(/https?:\/\/[^\s<]+/g, (match) => {
    let url = match;
    let suffix = "";
    while (/[)、。.,;:!?]$/.test(url)) {
      suffix = url.slice(-1) + suffix;
      url = url.slice(0, -1);
    }
    const href = unescapeHtml(url);
    return `<a href="${escapeAttr(href)}" target="_blank" rel="noopener">${url}</a>${suffix}`;
  });
}

function resolveUrl(rawHref, sourcePath, type) {
  const href = rawHref.trim().replace(/^<|>$/g, "");

  if (/^(https?:|mailto:|tel:|#)/i.test(href)) {
    return { url: href, internal: href.startsWith("#") };
  }

  const normalized = normalizeRelativePath(href, sourcePath);
  if (type === "link" && state.contentByPath.has(normalized)) {
    return { url: `#${encodeURIComponent(normalized)}`, internal: true };
  }

  const base = new URL(sourcePath, window.location.href);
  return { url: new URL(href, base).href, internal: false };
}

function normalizeRelativePath(href, sourcePath) {
  const pathOnly = href.split(/[?#]/)[0];
  if (!pathOnly || /^(https?:|mailto:|tel:)/i.test(pathOnly)) {
    return pathOnly;
  }

  const parts = sourcePath.split("/").slice(0, -1);
  pathOnly.split("/").forEach((part) => {
    if (!part || part === ".") return;
    if (part === "..") {
      parts.pop();
    } else {
      parts.push(part);
    }
  });

  return parts.join("/");
}

function normalizeText(value) {
  return String(value || "").toLowerCase().normalize("NFKC");
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;");
}

function unescapeHtml(value) {
  return String(value)
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"');
}

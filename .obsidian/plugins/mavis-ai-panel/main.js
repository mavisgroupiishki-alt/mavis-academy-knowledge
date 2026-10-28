const { ItemView, Plugin, PluginSettingTab, Setting, Notice, MarkdownRenderer } = require("obsidian");
const { spawn } = require("child_process");

const VIEW_TYPE = "mavis-ai-panel-view";
const DEFAULT_SETTINGS = {
  pythonCommand: "python3",
  assistantPath: "/Users/admin/MavisAI/mavis_ai.py",
  timeoutSeconds: 70,
};

class MavisAiView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() {
    return VIEW_TYPE;
  }

  getDisplayText() {
    return "Obsidian AI";
  }

  async onOpen() {
    this.render();
  }

  render() {
    const root = this.contentEl;
    root.empty();
    root.addClass("mavis-ai-panel");
    root.createEl("h3", { text: "Obsidian AI" });
    root.createEl("p", {
      text: "Спрашивайте по базе знаний и доступным данным Bitrix24. Ответы должны содержать источники.",
      cls: "mavis-ai-panel__hint",
    });

    const question = root.createEl("textarea", {
      attr: {
        placeholder: "Например: какие регламенты есть по работе с актами?",
        rows: "6",
        "aria-label": "Вопрос для Obsidian AI",
      },
    });
    const actions = root.createDiv({ cls: "mavis-ai-panel__actions" });
    const askButton = actions.createEl("button", { text: "Спросить", cls: "mod-cta" });
    const clearButton = actions.createEl("button", { text: "Очистить" });
    const result = root.createDiv({ cls: "mavis-ai-panel__result" });

    const ask = async () => {
      const value = question.value.trim();
      if (!value) {
        new Notice("Введите вопрос для Obsidian AI.");
        question.focus();
        return;
      }
      askButton.disabled = true;
      askButton.setText("Ищу…");
      result.empty();
      result.createEl("p", { text: "Obsidian AI ищет в базе и Bitrix24. Обычно до 60 секунд…" });
      try {
        const answer = await this.plugin.ask(value);
        result.empty();
        const answerEl = result.createDiv({ cls: "mavis-ai-panel__answer markdown-rendered" });
        await MarkdownRenderer.render(this.app, answer, answerEl, "", this);
      } catch (error) {
        result.empty();
        result.createEl("p", {
          text: "Ответ не получен за 60 секунд или очередь занята. Попробуйте ещё раз через минуту.",
          cls: "mavis-ai-panel__error",
        });
      } finally {
        askButton.disabled = false;
        askButton.setText("Спросить");
      }
    };

    askButton.addEventListener("click", ask);
    clearButton.addEventListener("click", () => {
      question.value = "";
      result.empty();
      question.focus();
    });
  }
}

class MavisAiSettingsTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const container = this.containerEl;
    container.empty();
    container.createEl("h2", { text: "Obsidian AI" });
    container.createEl("p", {
      text: "API-ключ VibeCode не хранится в Obsidian. Панель запускает только локальный Obsidian AI.",
    });
    new Setting(container)
      .setName("Команда Python")
      .setDesc("Обычно python3.")
      .addText((text) => text
        .setValue(this.plugin.settings.pythonCommand)
        .onChange(async (value) => {
          this.plugin.settings.pythonCommand = value.trim() || "python3";
          await this.plugin.saveSettings();
        }));
    new Setting(container)
      .setName("Путь к Obsidian AI")
      .setDesc("Локальный файл mavis_ai.py на этом компьютере.")
      .addText((text) => text
        .setValue(this.plugin.settings.assistantPath)
        .onChange(async (value) => {
          this.plugin.settings.assistantPath = value.trim();
          await this.plugin.saveSettings();
        }));
    new Setting(container)
      .setName("Тайм-аут ответа, секунд")
      .setDesc("Максимальное ожидание локального помощника.")
      .addText((text) => text
        .setValue(String(this.plugin.settings.timeoutSeconds))
        .onChange(async (value) => {
          const seconds = Number.parseInt(value, 10);
          this.plugin.settings.timeoutSeconds = Number.isFinite(seconds)
            ? Math.min(Math.max(seconds, 30), 300)
            : DEFAULT_SETTINGS.timeoutSeconds;
          await this.plugin.saveSettings();
        }));
  }
}

module.exports = class MavisAiPanelPlugin extends Plugin {
  async onload() {
    await this.loadSettings();
    this.registerView(VIEW_TYPE, (leaf) => new MavisAiView(leaf, this));
    this.addRibbonIcon("bot", "Открыть Obsidian AI", () => this.activateView());
    this.addCommand({
      id: "open-mavis-ai",
      name: "Открыть Obsidian AI",
      callback: () => this.activateView(),
    });
    this.addSettingTab(new MavisAiSettingsTab(this.app, this));
  }

  onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async activateView() {
    const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE);
    const leaf = existing[0] || this.app.workspace.getRightLeaf(false);
    await leaf.setViewState({ type: VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  ask(question) {
    return new Promise((resolve, reject) => {
      let output = "";
      let overflow = false;
      const child = spawn(
        this.settings.pythonCommand,
        [this.settings.assistantPath, "--ask", question],
        { shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] },
      );
      const timer = window.setTimeout(() => child.kill("SIGTERM"), this.settings.timeoutSeconds * 1000);
      child.stdout.on("data", (chunk) => {
        output += chunk.toString();
        if (output.length > 80000) {
          overflow = true;
          child.kill("SIGTERM");
        }
      });
      child.on("error", () => {
        window.clearTimeout(timer);
        reject(new Error("Obsidian AI process failed to start"));
      });
      child.on("close", (code) => {
        window.clearTimeout(timer);
        if (overflow) {
          reject(new Error("Obsidian AI response exceeded limit"));
        } else if (code !== 0) {
          reject(new Error("Obsidian AI returned an error"));
        } else {
          resolve(output.trim() || "Obsidian AI не вернул текстовый ответ.");
        }
      });
    });
  }
};
